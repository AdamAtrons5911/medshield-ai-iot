import numpy as np
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
import pickle
import os

class AnomalyDetector:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = "anomaly_model.keras"
        self.scaler_path = 'scaler.pkl'
        
    def generate_training_data(self, n_samples=5000):
        """Generate synthetic normal sensor data for training"""
        np.random.seed(42)
        
        # Normal ranges for each sensor
        # Temperature: 36.0 - 37.5°C
        # Humidity: 30 - 70%
        # Accelerometer: -2 to 2 g
        # Gyroscope: -50 to 50 deg/s
        
        temperature = np.random.normal(36.6, 0.3, n_samples)
        humidity = np.random.normal(50, 8, n_samples)
        accel_x = np.random.normal(0, 0.5, n_samples)
        accel_y = np.random.normal(0, 0.5, n_samples)
        accel_z = np.random.normal(9.8, 0.5, n_samples)  # gravity
        gyro_x = np.random.normal(0, 10, n_samples)
        gyro_y = np.random.normal(0, 10, n_samples)
        gyro_z = np.random.normal(0, 10, n_samples)
        
        data = np.column_stack([
            temperature, humidity, accel_x, accel_y, 
            accel_z, gyro_x, gyro_y, gyro_z
        ])
        
        return data
    
    def build_autoencoder(self, input_dim):
        """Build autoencoder neural network"""
        # Encoder
        encoder_input = keras.layers.Input(shape=(input_dim,))
        encoded = keras.layers.Dense(16, activation='relu')(encoder_input)
        encoded = keras.layers.Dense(8, activation='relu')(encoded)
        encoded = keras.layers.Dense(4, activation='relu')(encoded)
        
        # Decoder
        decoded = keras.layers.Dense(8, activation='relu')(encoded)
        decoded = keras.layers.Dense(16, activation='relu')(decoded)
        decoder_output = keras.layers.Dense(input_dim, activation='linear')(decoded)
        
        # Autoencoder model
        autoencoder = keras.Model(encoder_input, decoder_output)
        autoencoder.compile(optimizer='adam', loss='mse')
        
        return autoencoder
    
    def train(self):
        """Train the anomaly detection model"""
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            print("Loading existing model...")
            self.model = keras.models.load_model(self.model_path)
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            print("Model loaded successfully!")
            return
        
        print("Generating training data...")
        training_data = self.generate_training_data(5000)
        
        print("Scaling data...")
        training_data_scaled = self.scaler.fit_transform(training_data)
        
        print("Building autoencoder...")
        self.model = self.build_autoencoder(training_data.shape[1])
        
        print("Training model...")
        self.model.fit(
            training_data_scaled, 
            training_data_scaled,
            epochs=50,
            batch_size=32,
            validation_split=0.1,
            verbose=0
        )
        
        # Save model and scaler
        self.model.save("anomaly_model.keras")
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print("Model training complete and saved!")
    
    def check_anomaly(self, sensor_values):
        """
        Check if sensor values are anomalous
        
        Args:
            sensor_values: list of 8 values [temp, humidity, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z]
        
        Returns:
            (is_anomaly, anomaly_score): tuple of (bool, float)
        """
        if self.model is None:
            raise Exception("Model not trained. Call train() first.")
        
        # Prepare input
        input_data = np.array(sensor_values).reshape(1, -1)
        input_scaled = self.scaler.transform(input_data)
        
        # Get reconstruction
        reconstruction = self.model.predict(input_scaled, verbose=0)
        
        # Calculate reconstruction error (MSE)
        mse = np.mean(np.square(input_scaled - reconstruction))
        
        # Determine if anomaly
        is_anomaly = mse > self.threshold
        
        return is_anomaly, mse
    
    def set_threshold(self, new_threshold):
        """Adjust the anomaly detection threshold"""
        self.threshold = new_threshold
        print(f"Threshold updated to: {new_threshold}")

# Test the model
if __name__ == "__main__":
    detector = AnomalyDetector()
    detector.train()
    
    # Test with normal data
    normal_data = [36.5, 50, 0.1, 0.2, 9.8, 5, -3, 2]
    is_anomaly, score = detector.check_anomaly(normal_data)
    print(f"Normal data - Anomaly: {is_anomaly}, Score: {score:.6f}")
    
    # Test with abnormal data
    abnormal_data = [42.0, 90, 5.0, 5.0, 15.0, 100, 100, 100]
    is_anomaly, score = detector.check_anomaly(abnormal_data)
    print(f"Abnormal data - Anomaly: {is_anomaly}, Score: {score:.6f}")