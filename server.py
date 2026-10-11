from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os
from ai_model import AnomalyDetector

app = Flask(__name__)
CORS(app)

# Initialize database
DB_PATH = 'medshield.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create table if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            device_id TEXT NOT NULL,
            temperature REAL,
            humidity REAL,
            accel_x REAL,
            accel_y REAL,
            accel_z REAL,
            gyro_x REAL,
            gyro_y REAL,
            gyro_z REAL,
            anomaly_score REAL,
            is_emergency INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('DELETE FROM sensor_data')
    conn.commit()
    conn.close()


# Initialize AI model
detector = AnomalyDetector()
print("Training anomaly detector...")
detector.train()
print("Model ready!")

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/receive', methods=['POST'])
def receive_data():
    try:
        data = request.json
        
        # Extract sensor values
        sensor_values = [
            data.get('temperature', 0),
            data.get('humidity', 0),
            data.get('accel_x', 0),
            data.get('accel_y', 0),
            data.get('accel_z', 0),
            data.get('gyro_x', 0),
            data.get('gyro_y', 0),
            data.get('gyro_z', 0)
        ]
        
        # Check for anomaly
        is_anomaly, anomaly_score = detector.check_anomaly(sensor_values)
        
        # Store in database
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO sensor_data 
            (timestamp, device_id, temperature, humidity, accel_x, accel_y, accel_z, 
             gyro_x, gyro_y, gyro_z, anomaly_score, is_emergency)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('timestamp', datetime.now().isoformat()),
            data.get('device_id', 'unknown'),
            data.get('temperature'),
            data.get('humidity'),
            data.get('accel_x'),
            data.get('accel_y'),
            data.get('accel_z'),
            data.get('gyro_x'),
            data.get('gyro_y'),
            data.get('gyro_z'),
            float(anomaly_score),
            int(is_anomaly)
        ))
        conn.commit()
        conn.close()
        
        status = "EMERGENCY" if is_anomaly else "NORMAL"
        
        return jsonify({
            'status': 'success',
            'classification': status,
            'anomaly_score': float(anomaly_score),
            'message': f'Data received and classified as {status}'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/latest', methods=['GET'])
def get_latest():
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT id, timestamp, device_id, temperature, humidity, 
                   accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z,
                   anomaly_score, is_emergency, created_at
            FROM sensor_data
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        data = []
        for row in rows:
            data.append({
                'id': row[0],
                'timestamp': row[1],
                'device_id': row[2],
                'temperature': row[3],
                'humidity': row[4],
                'accel_x': row[5],
                'accel_y': row[6],
                'accel_z': row[7],
                'gyro_x': row[8],
                'gyro_y': row[9],
                'gyro_z': row[10],
                'anomaly_score': row[11],
                'is_emergency': row[12],
                'created_at': row[13]
            })
        
        return jsonify({
            'status': 'success',
            'count': len(data),
            'data': data
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM sensor_data')
        total_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM sensor_data WHERE is_emergency = 1')
        emergency_count = c.fetchone()[0]
        
        c.execute('SELECT AVG(anomaly_score) FROM sensor_data')
        avg_score = c.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'total_packets': total_count,
            'emergency_count': emergency_count,
            'normal_count': total_count - emergency_count,
            'avg_anomaly_score': float(avg_score)
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("MedShield Server Starting...")
    print("=" * 60)
    print("Server running at: http://localhost:5000")
    print("Dashboard: http://localhost:5000")
    print("API Endpoint: http://localhost:5000/api/receive")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)