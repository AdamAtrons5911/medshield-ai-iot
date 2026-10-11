import requests
import time
import random
import numpy as np
from datetime import datetime
import json

class MedicalDeviceSimulator:
    def __init__(self, server_url='http://localhost:5000', device_id='SIM-001'):
        self.server_url = server_url
        self.device_id = device_id
        self.packet_count = 0
        
    def generate_normal_data(self):
        """Generate normal sensor readings"""
        return {
            'device_id': self.device_id,
            'timestamp': datetime.now().isoformat(),
            'temperature': round(np.random.normal(36.6, 0.3), 2),
            'humidity': round(np.random.normal(50, 8), 2),
            'accel_x': round(np.random.normal(0, 0.5), 3),
            'accel_y': round(np.random.normal(0, 0.5), 3),
            'accel_z': round(np.random.normal(9.8, 0.5), 3),
            'gyro_x': round(np.random.normal(0, 10), 2),
            'gyro_y': round(np.random.normal(0, 10), 2),
            'gyro_z': round(np.random.normal(0, 10), 2)
        }
    
    def generate_anomaly_data(self):
        """Generate anomalous sensor readings"""
        anomaly_type = random.choice(['fever', 'fall', 'seizure', 'extreme_humidity'])
        
        if anomaly_type == 'fever':
            data = self.generate_normal_data()
            data['temperature'] = round(random.uniform(38.5, 41.0), 2)
            print(f"⚠️  INJECTING ANOMALY: High fever ({data['temperature']}°C)")
            
        elif anomaly_type == 'fall':
            data = self.generate_normal_data()
            data['accel_x'] = round(random.uniform(-5, 5), 3)
            data['accel_y'] = round(random.uniform(-5, 5), 3)
            data['accel_z'] = round(random.uniform(-3, 20), 3)
            print(f"⚠️  INJECTING ANOMALY: Fall detected (high acceleration)")
            
        elif anomaly_type == 'seizure':
            data = self.generate_normal_data()
            data['gyro_x'] = round(random.uniform(-150, 150), 2)
            data['gyro_y'] = round(random.uniform(-150, 150), 2)
            data['gyro_z'] = round(random.uniform(-150, 150), 2)
            print(f"⚠️  INJECTING ANOMALY: Seizure-like motion (high gyro)")
            
        else:  # extreme_humidity
            data = self.generate_normal_data()
            data['humidity'] = round(random.uniform(85, 100), 2)
            print(f"⚠️  INJECTING ANOMALY: Extreme humidity ({data['humidity']}%)")
        
        return data
    
    def send_data(self, data):
        """Send data to server"""
        try:
            response = requests.post(
                f'{self.server_url}/api/receive',
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('classification', 'UNKNOWN')
                score = result.get('anomaly_score', 0)
                
                if status == 'EMERGENCY':
                    print(f"🚨 EMERGENCY DETECTED! Score: {score:.6f}")
                else:
                    print(f"✓ Packet #{self.packet_count} sent - Status: {status}, Score: {score:.6f}")
                
                return True
            else:
                print(f"✗ Server error: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def run(self, interval=1.5, anomaly_probability=0.05):
        """
        Run the simulator
        
        Args:
            interval: seconds between packets
            anomaly_probability: probability of generating anomaly (0-1)
        """
        print("=" * 70)
        print("MedShield Device Simulator Started")
        print("=" * 70)
        print(f"Device ID: {self.device_id}")
        print(f"Server: {self.server_url}")
        print(f"Interval: {interval}s")
        print(f"Anomaly probability: {anomaly_probability * 100}%")
        print("=" * 70)
        print("Sending data... (Press Ctrl+C to stop)")
        print()
        
        try:
            while True:
                self.packet_count += 1
                
                # Decide if this packet should be anomalous
                if random.random() < anomaly_probability:
                    data = self.generate_anomaly_data()
                else:
                    data = self.generate_normal_data()
                
                # Send to server
                self.send_data(data)
                
                # Wait before next packet
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n")
            print("=" * 70)
            print("Simulator stopped by user")
            print(f"Total packets sent: {self.packet_count}")
            print("=" * 70)

if __name__ == "__main__":
    simulator = MedicalDeviceSimulator()
    
    # Run with default settings: send packet every 1.5s, 5% anomaly rate
    simulator.run(interval=1.5, anomaly_probability=0.05)
    
    # Alternative configurations:
    # simulator.run(interval=1.0, anomaly_probability=0.1)  # faster, more anomalies
    # simulator.run(interval=2.0, anomaly_probability=0.02)  # slower, fewer anomalies