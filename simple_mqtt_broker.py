#!/usr/bin/env python3
"""
Simple MQTT Broker using mosquitto command
This script helps you start the mosquitto broker easily
"""

import subprocess
import sys
import os

def find_mosquitto():
    """Try to find mosquitto executable"""
    common_paths = [
        "mosquitto",
        "C:\\Program Files\\mosquitto\\mosquitto.exe",
        "C:\\Program Files (x86)\\mosquitto\\mosquitto.exe",
        os.path.expanduser("~/mosquitto/mosquitto.exe"),
    ]
    
    for path in common_paths:
        try:
            # Test if mosquitto exists
            result = subprocess.run([path, "--help"], 
                                  capture_output=True, 
                                  timeout=2)
            if result.returncode == 0 or "mosquitto" in result.stdout.decode().lower():
                return path
        except:
            continue
    
    return None

def start_broker():
    """Start the MQTT broker"""
    mosquitto_path = find_mosquitto()
    
    if mosquitto_path:
        print(f"Found mosquitto at: {mosquitto_path}")
        print("Starting MQTT Broker on port 1883...")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        try:
            subprocess.run([mosquitto_path, "-v"])
        except KeyboardInterrupt:
            print("\nBroker stopped")
    else:
        print("ERROR: Could not find mosquitto executable!")
        print("\nPlease do one of the following:")
        print("1. Download mosquitto from: https://mosquitto.org/download/")
        print("2. Install using: choco install mosquitto")
        print("3. Manually run: mosquitto -v")
        sys.exit(1)

if __name__ == '__main__':
    start_broker()

