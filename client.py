import os
import paho.mqtt.client as mqtt
import sqlite3
import csv
from dotenv import load_dotenv
import threading
import sys
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLineEdit, QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject
from cryptography.fernet import Fernet
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions

# Load environment variables from the configuration file
load_dotenv('config.env')

# Define the MQTT settings
broker = "605fcb0081be4a56b155b8f5d562e5d6.s1.eu.hivemq.cloud"
port = 8883
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
client_id = "zT4vYN89EU"
# Subscribe to all topics
wildcard_topic = "#"

# Global flag to control thread running state
running = True

# Global variable to track last state
last_states = {}

# MQTT client setup
client = mqtt.Client(client_id=client_id)
client.username_pw_set(username, password)
client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

# Create a PyQt5 signal to update the GUI from the MQTT callbacks
class MqttSignal(QObject):
    message_received = pyqtSignal(str, str)
    log_message = pyqtSignal(str)

mqtt_signal = MqttSignal()

# Load the encryption key from the file
with open('encryption_key.key', 'rb') as key_file:
    encryption_key = key_file.read()

cipher_suite = Fernet(encryption_key)

# Set up InfluxDB client for InfluxDB Cloud
influxdb_url = os.getenv("INFLUXDB_URL")
influxdb_token = os.getenv("INFLUXDB_TOKEN")
influxdb_org = os.getenv("INFLUXDB_ORG")
influxdb_bucket = os.getenv("INFLUXDB_BUCKET")

influx_client = InfluxDBClient(url=influxdb_url, token=influxdb_token)
write_api = influx_client.write_api(write_options=WriteOptions(write_type=SYNCHRONOUS))

# Function to encrypt messages
def encrypt_message(message):
    return cipher_suite.encrypt(message.encode())

# Function to decrypt messages
def decrypt_message(encrypted_message):
    return cipher_suite.decrypt(encrypted_message).decode()

# Function to save messages to the database
def save_message_to_db(topic, message):
    try:
        encrypted_message = encrypt_message(message)
        conn = sqlite3.connect('mqtt_messages.db')
        c = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                message BLOB NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            INSERT INTO messages (topic, message, timestamp) VALUES (?, ?, ?)
        ''', (topic, encrypted_message, current_time))
        conn.commit()
        conn.close()
        mqtt_signal.log_message.emit(f"Saved encrypted message to DB: {message} from topic: {topic}")
    except Exception as e:
        mqtt_signal.log_message.emit(f"Error saving to DB: {e}")

# Function to save messages to a CSV file
def save_message_to_csv(topic, message):
    try:
        encrypted_message = encrypt_message(message).decode()
        file_exists = os.path.isfile('mqtt_messages.csv')
        with open('mqtt_messages.csv', mode='a', newline='') as csvfile:
            fieldnames = ['topic', 'message', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({'topic': topic, 'message': encrypted_message, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        mqtt_signal.log_message.emit(f"Saved encrypted message to CSV: {message} from topic: {topic}")
    except Exception as e:
        mqtt_signal.log_message.emit(f"Error saving to CSV: {e}")

# Function to save messages to InfluxDB
def save_message_to_influxdb(topic, message):
    try:
        point = Point("mqtt_messages").tag("topic", topic).field("message", message).time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(bucket=influxdb_bucket, org=influxdb_org, record=point)
        mqtt_signal.log_message.emit(f"Saved message to InfluxDB: {message} from topic: {topic}")
    except Exception as e:
        mqtt_signal.log_message.emit(f"Error saving to InfluxDB: {e}")

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt_signal.log_message.emit("Connected to MQTT Broker!")
        client.subscribe(wildcard_topic)
    else:
        mqtt_signal.log_message.emit(f"Failed to connect, return code {rc}\n")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    received_message = msg.payload.decode()
    mqtt_signal.message_received.emit(msg.topic, received_message)

    if msg.topic not in last_states or last_states[msg.topic] != received_message:
        last_states[msg.topic] = received_message
        save_message_to_db(msg.topic, received_message)
        save_message_to_csv(msg.topic, received_message)
        save_message_to_influxdb(msg.topic, received_message)

client.on_connect = on_connect
client.on_message = on_message

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MQTT Client")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.in_state_label = QLabel("Current In State: N/A")
        self.out_state_label = QLabel("Current Out State: N/A")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Enter topic")

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message")

        self.publish_button = QPushButton("Publish")
        self.publish_button.clicked.connect(self.publish_message)

        layout.addWidget(self.in_state_label)
        layout.addWidget(self.out_state_label)
        layout.addWidget(self.log_box)
        layout.addWidget(self.topic_input)
        layout.addWidget(self.message_input)
        layout.addWidget(self.publish_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        mqtt_signal.message_received.connect(self.update_state_display)
        mqtt_signal.log_message.connect(self.log_message)

    def update_state_display(self, topic, message):
        if topic == "ACE/ACE/InBitC1":
            self.in_state_label.setText(f"Current In State: {message}")
        elif topic == "ACE/ACE/OutBitD1":
            self.out_state_label.setText(f"Current Out State: {message}")

    def log_message(self, message):
        self.log_box.append(message)

    def publish_message(self):
        topic = self.topic_input.text()
        message = self.message_input.text()
        if topic and message:
            client.publish(topic, message, retain=True)
            self.log_message(f"Published message: {message} to topic: {topic}")
            self.topic_input.clear()
            self.message_input.clear()
        else:
            QMessageBox.warning(self, "Input Error", "Both topic and message must be provided")

def start_mqtt():
    client.connect(broker, port)
    client.loop_start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    mqtt_thread = threading.Thread(target=start_mqtt)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    sys.exit(app.exec_())
