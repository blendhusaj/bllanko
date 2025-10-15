#!/usr/bin/env python3
"""
Car2X Dashboard Web Application
A modern web interface for V2X communication and vehicle management.
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Any
import os

# Optional: load environment variables if a .env file is present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '*')
socketio = SocketIO(app, cors_allowed_origins=CORS_ALLOWED_ORIGINS)

MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', '1883'))

class Car2XDashboard:
    def __init__(self):
        self.mqtt_client = mqtt.Client()
        self.vehicles = {}
        self.infrastructure = {}
        self.emergencies = []
        self.jobs = {}
        self.setup_mqtt()
        
    def setup_mqtt(self):
        """Setup MQTT client for receiving V2X messages"""
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
    def on_mqtt_connect(self, client, userdata, flags, rc):
        print(f"MQTT Connected with result code {rc}")
        # Subscribe to all V2X topics
        client.subscribe("v2x/vehicles/+/status")
        client.subscribe("v2x/vehicles/+/emergency")
        client.subscribe("v2x/infrastructure/+")
        client.subscribe("v2x/emergency/broadcast")
        client.subscribe("v2x/jobs/+/response")
        
    def on_mqtt_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            message = json.loads(msg.payload.decode())
            
            if topic_parts[1] == "vehicles" and topic_parts[3] == "status":
                # Vehicle status update
                vehicle_id = topic_parts[2]
                self.vehicles[vehicle_id] = message
                socketio.emit('vehicle_update', message)
                
            elif topic_parts[1] == "vehicles" and topic_parts[3] == "emergency":
                # Vehicle emergency
                vehicle_id = topic_parts[2]
                socketio.emit('vehicle_emergency', {
                    'vehicle_id': vehicle_id,
                    'message': message
                })
                
            elif topic_parts[1] == "infrastructure":
                # Infrastructure update
                infra_id = topic_parts[2]
                self.infrastructure[infra_id] = message
                socketio.emit('infrastructure_update', message)
                
            elif topic_parts[1] == "emergency":
                # Emergency broadcast
                self.emergencies.append(message)
                socketio.emit('emergency_alert', message)
                
            elif topic_parts[1] == "jobs":
                # Job response
                job_id = topic_parts[2]
                if job_id in self.jobs:
                    self.jobs[job_id]['responses'] = self.jobs[job_id].get('responses', [])
                    self.jobs[job_id]['responses'].append(message)
                    socketio.emit('job_response', {
                        'job_id': job_id,
                        'response': message
                    })
                    
        except Exception as e:
            print(f"Error processing MQTT message: {e}")
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.mqtt_client.loop_start()
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT: {e}")
            return False
    
    def create_job(self, job_type: str, target_vehicles: List[str], parameters: Dict[str, Any] = None):
        """Create and distribute a job"""
        import uuid
        job_id = str(uuid.uuid4())[:8]
        
        job = {
            "job_id": job_id,
            "type": job_type,
            "timestamp": datetime.now().isoformat(),
            "target_vehicles": target_vehicles,
            "parameters": parameters or {},
            "status": "pending"
        }
        
        self.jobs[job_id] = job
        
        # Publish job to MQTT
        self.mqtt_client.publish(f"v2x/jobs/{job_id}/assign", json.dumps(job))
        
        return job_id

# Global dashboard instance
dashboard = Car2XDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/vehicles')
def get_vehicles():
    """Get all vehicle data"""
    return jsonify(dashboard.vehicles)

@app.route('/api/infrastructure')
def get_infrastructure():
    """Get all infrastructure data"""
    return jsonify(dashboard.infrastructure)

@app.route('/api/emergencies')
def get_emergencies():
    """Get recent emergencies"""
    return jsonify(dashboard.emergencies[-10:])  # Last 10 emergencies

@app.route('/api/jobs')
def get_jobs():
    """Get all jobs"""
    return jsonify(dashboard.jobs)

@app.route('/api/create_job', methods=['POST'])
def create_job():
    """Create a new job"""
    data = request.get_json()
    job_id = dashboard.create_job(
        data.get('type'),
        data.get('target_vehicles', []),
        data.get('parameters', {})
    )
    return jsonify({'job_id': job_id, 'status': 'created'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'data': 'Connected to Car2X Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_data')
def handle_data_request():
    """Send current data to client"""
    emit('initial_data', {
        'vehicles': dashboard.vehicles,
        'infrastructure': dashboard.infrastructure,
        'emergencies': dashboard.emergencies[-10:],
        'jobs': dashboard.jobs
    })

if __name__ == '__main__':
    # Connect to MQTT
    if dashboard.connect_mqtt():
        print("Starting Car2X Dashboard...")
        host = os.getenv('HOST', '0.0.0.0')
        port = int(os.getenv('PORT', '5000'))
        debug = os.getenv('FLASK_DEBUG', '0') == '1'
        socketio.run(app, debug=debug, host=host, port=port)
    else:
        print("Failed to connect to MQTT broker. Please start the V2X simulator first.")
