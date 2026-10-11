/*
 * MedShield - Medical Wearable Device Example
 * Hardware: ESP32 or Arduino with WiFi/Ethernet shield
 * Sensors: DHT22 (temp/humidity), MPU6050 (accel/gyro)
 * 
 * This code demonstrates how real hardware would connect to MedShield server
 * NOTE: This is reference code only - no hardware required for simulation
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <Wire.h>
#include <MPU6050.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server configuration
const char* serverURL = "http://YOUR_SERVER_IP:5000/api/receive";
const char* deviceID = "ESP32-001";

// Sensor pins
#define DHT_PIN 4
#define DHT_TYPE DHT22

// Sensor objects
DHT dht(DHT_PIN, DHT_TYPE);
MPU6050 mpu;

// Timing
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 2000; // Send every 2 seconds

void setup() {
  Serial.begin(115200);
  Serial.println("MedShield Device Starting...");
  
  // Initialize WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Initialize sensors
  dht.begin();
  Wire.begin();
  mpu.initialize();
  
  if (mpu.testConnection()) {
    Serial.println("MPU6050 connected successfully");
  } else {
    Serial.println("MPU6050 connection failed");
  }
  
  Serial.println("Device ready!");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Send data at specified interval
  if (currentTime - lastSendTime >= sendInterval) {
    sendSensorData();
    lastSendTime = currentTime;
  }
}

void sendSensorData() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    
    // Read sensors
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    
    int16_t ax, ay, az;
    int16_t gx, gy, gz;
    mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
    
    // Convert raw values to standard units
    float accel_x = ax / 16384.0; // Convert to g
    float accel_y = ay / 16384.0;
    float accel_z = az / 16384.0;
    float gyro_x = gx / 131.0;    // Convert to deg/s
    float gyro_y = gy / 131.0;
    float gyro_z = gz / 131.0;
    
    // Create JSON payload
    StaticJsonDocument<512> doc;
    doc["device_id"] = deviceID;
    doc["timestamp"] = getTimestamp();
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
    doc["accel_x"] = accel_x;
    doc["accel_y"] = accel_y;
    doc["accel_z"] = accel_z;
    doc["gyro_x"] = gyro_x;
    doc["gyro_y"] = gyro_y;
    doc["gyro_z"] = gyro_z;
    
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    
    // Send HTTP POST
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");
    
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
      String response = http.getString();
      Serial.println("Server response: " + response);
      
      // Parse response
      StaticJsonDocument<256> responseDoc;
      deserializeJson(responseDoc, response);
      
      String classification = responseDoc["classification"];
      if (classification == "EMERGENCY") {
        Serial.println("⚠️ EMERGENCY DETECTED!");
        // Trigger alert (LED, buzzer, etc.)
      } else {
        Serial.println("✓ Data sent - Status: NORMAL");
      }
    } else {
      Serial.print("Error sending data: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  } else {
    Serial.println("WiFi disconnected");
  }
}

String getTimestamp() {
  // In production, use NTP or RTC module for accurate timestamps
  return String(millis());
}