#!/usr/bin/env python3
"""
Car2X V2X Message Simulator
Simulates V2X communication using MQTT for vehicle-to-vehicle and vehicle-to-infrastructure communication.
"""

import json
import time
import random
import threading
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from typing import Dict, List, Any
import uuid

class V2XSimulator:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client()
        self.running = False
        self.vehicles = {}
        self.infrastructure = {}
        self.jobs = {}
        
        # Setup MQTT callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")
        # Subscribe to vehicle topics
        client.subscribe("v2x/vehicles/+/status")
        client.subscribe("v2x/vehicles/+/emergency")
        client.subscribe("v2x/jobs/+/assign")
        client.subscribe("v2x/jobs/+/response")
        
    def on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split('/')
            message = json.loads(msg.payload.decode())
            
            if topic_parts[1] == "vehicles" and topic_parts[3] == "status":
                vehicle_id = topic_parts[2]
                self.vehicles[vehicle_id] = message
                
            elif topic_parts[1] == "vehicles" and topic_parts[3] == "emergency":
                vehicle_id = topic_parts[2]
                self.handle_emergency_message(vehicle_id, message)
                
            elif topic_parts[1] == "jobs" and topic_parts[3] == "assign":
                job_id = topic_parts[2]
                self.handle_job_assignment(job_id, message)
                
            elif topic_parts[1] == "jobs" and topic_parts[3] == "response":
                job_id = topic_parts[2]
                self.handle_job_response(job_id, message)
                
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def start(self):
        """Start the V2X simulator"""
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
        self.running = True
        
        # Start simulation threads
        threading.Thread(target=self.simulate_vehicles, daemon=True).start()
        threading.Thread(target=self.simulate_infrastructure, daemon=True).start()
        threading.Thread(target=self.simulate_emergency_events, daemon=True).start()
        
        print("V2X Simulator started")
    
    def stop(self):
        """Stop the V2X simulator"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print("V2X Simulator stopped")
    
    def simulate_vehicles(self):
        """Simulate vehicle movement and CAM (Cooperative Awareness Message) generation"""
        vehicle_ids = ["V001", "V002", "V003", "V004", "V005"]
        
        # Initialize vehicle positions (Munich area)
        base_lat, base_lon = 48.1351, 11.5820
        
        for i, vid in enumerate(vehicle_ids):
            self.vehicles[vid] = {
                "vehicle_id": vid,
                "timestamp": datetime.now().isoformat(),
                "position": {
                    "latitude": base_lat + random.uniform(-0.01, 0.01),
                    "longitude": base_lon + random.uniform(-0.01, 0.01)
                },
                "speed": random.uniform(30, 80),  # km/h
                "heading": random.uniform(0, 360),
                "status": "normal"
            }
        
        while self.running:
            for vid in vehicle_ids:
                if vid in self.vehicles:
                    # Update vehicle position
                    vehicle = self.vehicles[vid]
                    vehicle["timestamp"] = datetime.now().isoformat()
                    
                    # Simulate movement
                    speed_kmh = vehicle["speed"]
                    speed_ms = speed_kmh / 3.6
                    
                    # Update position based on speed and heading
                    heading_rad = vehicle["heading"] * 3.14159 / 180
                    lat_offset = (speed_ms * 0.00001) * random.uniform(-0.5, 0.5)
                    lon_offset = (speed_ms * 0.00001) * random.uniform(-0.5, 0.5)
                    
                    vehicle["position"]["latitude"] += lat_offset
                    vehicle["position"]["longitude"] += lon_offset
                    
                    # Occasionally change heading
                    if random.random() < 0.1:
                        vehicle["heading"] = (vehicle["heading"] + random.uniform(-30, 30)) % 360
                    
                    # Publish CAM message
                    self.publish_cam_message(vehicle)
            
            time.sleep(1)  # Update every second
    
    def simulate_infrastructure(self):
        """Simulate infrastructure messages (traffic lights, road signs, etc.)"""
        traffic_lights = [
            {"id": "TL001", "position": {"lat": 48.1351, "lon": 11.5820}, "state": "red"},
            {"id": "TL002", "position": {"lat": 48.1361, "lon": 11.5830}, "state": "green"},
            {"id": "TL003", "position": {"lat": 48.1371, "lon": 11.5840}, "state": "yellow"}
        ]
        
        while self.running:
            for tl in traffic_lights:
                # Simulate traffic light state changes
                if random.random() < 0.05:  # 5% chance to change state
                    states = ["red", "yellow", "green"]
                    tl["state"] = random.choice(states)
                
                # Publish infrastructure message
                message = {
                    "type": "V2I",
                    "infrastructure_id": tl["id"],
                    "timestamp": datetime.now().isoformat(),
                    "position": tl["position"],
                    "data": {
                        "traffic_light_state": tl["state"],
                        "remaining_time": random.randint(5, 30)
                    }
                }
                
                self.client.publish(f"v2x/infrastructure/{tl['id']}", json.dumps(message))
            
            time.sleep(2)  # Update every 2 seconds
    
    def simulate_emergency_events(self):
        """Simulate emergency events and DENM (Decentralized Environmental Notification) messages"""
        emergency_types = [
            "accident", "traffic_jam", "road_closure", "hazardous_weather", "emergency_vehicle"
        ]
        
        while self.running:
            if random.random() < 0.15:  # 15% chance of emergency event (increased for demo)
                emergency_type = random.choice(emergency_types)
                self.create_emergency_event(emergency_type)
            
            time.sleep(5)  # Check every 5 seconds
    
    def create_emergency_event(self, event_type: str):
        """Create an emergency event and broadcast DENM message"""
        event_id = str(uuid.uuid4())[:8]
        
        # Random position near Munich
        base_lat, base_lon = 48.1351, 11.5820
        position = {
            "latitude": base_lat + random.uniform(-0.02, 0.02),
            "longitude": base_lon + random.uniform(-0.02, 0.02)
        }
        
        denm_message = {
            "type": "DENM",
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "position": position,
            "event_type": event_type,
            "severity": random.choice(["low", "medium", "high"]),
            "duration": random.randint(300, 1800),  # 5-30 minutes
            "radius": random.randint(100, 1000)  # meters
        }
        
        # Broadcast to all vehicles
        self.client.publish("v2x/emergency/broadcast", json.dumps(denm_message))
        print(f"Emergency event created: {event_type} at {position}")
    
    def publish_cam_message(self, vehicle: Dict[str, Any]):
        """Publish Cooperative Awareness Message (CAM)"""
        cam_message = {
            "type": "CAM",
            "vehicle_id": vehicle["vehicle_id"],
            "timestamp": vehicle["timestamp"],
            "position": vehicle["position"],
            "speed": vehicle["speed"],
            "heading": vehicle["heading"],
            "status": vehicle["status"]
        }
        
        self.client.publish(f"v2x/vehicles/{vehicle['vehicle_id']}/status", json.dumps(cam_message))
    
    def create_job(self, job_type: str, target_vehicles: List[str], parameters: Dict[str, Any] = None):
        """Create a job and distribute it to target vehicles"""
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
        
        # Distribute job to target vehicles
        for vehicle_id in target_vehicles:
            self.client.publish(f"v2x/jobs/{job_id}/assign", json.dumps(job))
        
        print(f"Job created: {job_type} for vehicles {target_vehicles}")
        return job_id
    
    def handle_emergency_message(self, vehicle_id: str, message: Dict[str, Any]):
        """Handle emergency messages from vehicles"""
        print(f"Emergency from {vehicle_id}: {message}")
    
    def handle_job_assignment(self, job_id: str, job_data: Dict[str, Any]):
        """Handle job assignments and simulate vehicle responses"""
        print(f"Job {job_id} assigned to vehicles")
        
        # Simulate vehicle responses after a short delay
        def send_responses():
            time.sleep(2)  # Wait 2 seconds before responding
            for vehicle_id in job_data.get('target_vehicles', []):
                response = {
                    "job_id": job_id,
                    "vehicle_id": vehicle_id,
                    "status": "acknowledged",
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Job received and processing"
                }
                self.client.publish(f"v2x/jobs/{job_id}/response", json.dumps(response))
                print(f"Vehicle {vehicle_id} responded to job {job_id}")
        
        # Start response thread
        threading.Thread(target=send_responses, daemon=True).start()
    
    def handle_job_response(self, job_id: str, response: Dict[str, Any]):
        """Handle job responses from vehicles"""
        if job_id in self.jobs:
            self.jobs[job_id]["responses"] = self.jobs[job_id].get("responses", [])
            self.jobs[job_id]["responses"].append(response)
            print(f"Job {job_id} response: {response}")

if __name__ == "__main__":
    simulator = V2XSimulator()
    
    try:
        simulator.start()
        
        # Create some example jobs
        time.sleep(2)
        simulator.create_job("diagnostic", ["V001", "V002"], {"sensors": ["engine", "brakes"]})
        simulator.create_job("navigation", ["V003"], {"destination": "Munich Airport"})
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        simulator.stop()
