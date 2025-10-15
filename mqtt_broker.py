#!/usr/bin/env python3
"""
Simple MQTT Broker for Car2X System
Uses hbmqtt as a pure Python MQTT broker
"""

import asyncio
import logging
from hbmqtt.broker import Broker

# Configure logging
logging.basicConfig(level=logging.INFO)

# MQTT Broker configuration
config = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'bind': '0.0.0.0:1883',
        },
    },
    'sys_interval': 10,
    'auth': {
        'allow-anonymous': True,
    },
}

async def broker_coro():
    broker = Broker(config)
    await broker.start()
    print("MQTT Broker started on port 1883")
    print("Press Ctrl+C to stop")
    
    # Keep the broker running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping MQTT Broker...")
    finally:
        await broker.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(broker_coro())
    except KeyboardInterrupt:
        print("\nBroker stopped")

