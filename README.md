# Car2X Dashboard - V2X Communication System

A comprehensive Car2X (Car-to-Everything) communication system that simulates V2X technology with a modern web dashboard interface. This system provides real-time vehicle-to-vehicle (V2V), vehicle-to-infrastructure (V2I), and vehicle-to-network (V2N) communication capabilities.

## Features

### 🚗 V2X Communication
- **Vehicle-to-Vehicle (V2V)**: Real-time position and status sharing
- **Vehicle-to-Infrastructure (V2I)**: Traffic light communication and road condition updates
- **Emergency Broadcasting**: DENM (Decentralized Environmental Notification) messages
- **MQTT-based Job System**: Remote vehicle management and task distribution

### 🎛️ Dashboard Features
- **Real-time Map**: Interactive map showing vehicle positions and infrastructure
- **Live Vehicle Tracking**: Speed, heading, and status monitoring
- **Emergency Alerts**: Real-time safety notifications and warnings
- **Traffic Management**: Traffic light status and timing information
- **Job Management**: Create and monitor remote vehicle tasks
- **Statistics**: Live metrics and system status

### 🔧 Technical Features
- **MQTT Communication**: Lightweight, efficient message transport
- **WebSocket Integration**: Real-time dashboard updates
- **Modular Architecture**: Easy to extend and customize
- **Responsive Design**: Works on desktop and mobile devices

## Installation

### Prerequisites
- Python 3.7+
- MQTT Broker (Mosquitto recommended)

### Setup

1. **Clone or download the project files**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install and start MQTT Broker (Mosquitto):**
   
   **Windows:**
   ```bash
   # Download from https://mosquitto.org/download/
   # Or use chocolatey:
   choco install mosquitto
   
   # Start the broker
   mosquitto -v
   ```
   
   **Linux/macOS:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mosquitto mosquitto-clients
   
   # macOS with Homebrew
   brew install mosquitto
   
   # Start the broker
   mosquitto -v
   ```

## Usage

### 1. Start the V2X Simulator
```bash
python v2x_simulator.py
```
This will start the MQTT-based V2X message simulator that generates:
- Vehicle movement and CAM (Cooperative Awareness Messages)
- Traffic light status updates
- Emergency events and DENM messages
- Job distribution system

### 2. Start the Web Dashboard
```bash
python app.py
```
This will start the Flask web application on `http://localhost:5000`

### 3. Open the Dashboard
Open your web browser and navigate to `http://localhost:5000`

## Configuration

You can configure the app via environment variables (optionally using a `.env` file):

- `SECRET_KEY` — Flask secret key (default: `change-me`)
- `MQTT_BROKER_HOST` — MQTT host (default: `localhost`)
- `MQTT_BROKER_PORT` — MQTT port (default: `1883`)
- `HOST` — Flask bind host (default: `0.0.0.0`)
- `PORT` — Flask port (default: `5000`)
- `FLASK_DEBUG` — set to `1` to enable debug (default: `0`)
- `CORS_ALLOWED_ORIGINS` — Socket.IO CORS origins (default: `*`)

Security notes:
- Do not commit real secrets. Use `.env` locally and keep it out of version control.
- Keep debug disabled in production (`FLASK_DEBUG=0`).
- Public MQTT brokers or anonymous access are for demos only.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   V2X Simulator │    │  MQTT Broker    │    │  Web Dashboard  │
│                 │    │                 │    │                 │
│ • Vehicle CAM   │◄──►│ • Message Queue │◄──►│ • Real-time UI  │
│ • Infrastructure│    │ • Topic Routing │    │ • Map Display   │
│ • Emergency DENM│    │ • QoS Support   │    │ • Job Management│
│ • Job System    │    │                 │    │ • Statistics    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## V2X Message Types

### CAM (Cooperative Awareness Message)
```json
{
  "type": "CAM",
  "vehicle_id": "V001",
  "timestamp": "2024-01-01T12:00:00Z",
  "position": {"latitude": 48.1351, "longitude": 11.5820},
  "speed": 65.5,
  "heading": 45.0,
  "status": "normal"
}
```

### DENM (Decentralized Environmental Notification)
```json
{
  "type": "DENM",
  "event_id": "E001",
  "timestamp": "2024-01-01T12:00:00Z",
  "position": {"latitude": 48.1351, "longitude": 11.5820},
  "event_type": "accident",
  "severity": "high",
  "duration": 1800,
  "radius": 500
}
```

### Job Messages
```json
{
  "job_id": "J001",
  "type": "diagnostic",
  "timestamp": "2024-01-01T12:00:00Z",
  "target_vehicles": ["V001", "V002"],
  "parameters": {"sensors": ["engine", "brakes"]},
  "status": "pending"
}
```

## Customization

### Adding New Vehicle Types
Modify `v2x_simulator.py` to add different vehicle behaviors:
```python
def simulate_emergency_vehicle(self):
    # Add emergency vehicle simulation
    pass
```

### Extending Dashboard Features
Add new widgets in `templates/index.html` and corresponding JavaScript in `static/js/app.js`

### Custom V2X Messages
Implement new message types by extending the simulator and dashboard message handlers.

## MQTT Topics

- `v2x/vehicles/{vehicle_id}/status` - Vehicle status updates
- `v2x/vehicles/{vehicle_id}/emergency` - Vehicle emergency messages
- `v2x/infrastructure/{infra_id}` - Infrastructure updates
- `v2x/emergency/broadcast` - Emergency broadcasts
- `v2x/jobs/{job_id}/assign` - Job assignments
- `v2x/jobs/{job_id}/response` - Job responses

## Safety Features

- **Collision Warning**: Vehicles share position data for collision avoidance
- **Emergency Response**: Real-time emergency vehicle notifications
- **Traffic Management**: Smart traffic light coordination
- **Hazard Detection**: Road condition and weather warnings

## Future Enhancements

- **5G Integration**: High-bandwidth V2X communication
- **Machine Learning**: Predictive traffic analysis
- **Autonomous Vehicle Support**: Enhanced V2X for self-driving cars
- **Blockchain Security**: Secure V2X message authentication
- **Edge Computing**: Local V2X processing and decision making

## Troubleshooting

### MQTT Connection Issues
- Ensure Mosquitto broker is running
- Check firewall settings for port 1883
- Verify broker configuration

### Dashboard Not Loading
- Check if Flask app is running on port 5000
- Verify all dependencies are installed
- Check browser console for JavaScript errors

### No Vehicle Data
- Ensure V2X simulator is running
- Check MQTT broker connectivity
- Verify topic subscriptions

## License

This project is for educational and demonstration purposes. Feel free to modify and extend for your own Car2X projects.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

