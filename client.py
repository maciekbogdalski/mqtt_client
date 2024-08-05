import os
import paho.mqtt.client as mqtt
import sqlite3
import csv
from dotenv import load_dotenv
import time
import threading
import signal
import sys

# Load environment variables from the configuration file
load_dotenv('config.env')

# Define the MQTT settings
broker = "605fcb0081be4a56b155b8f5d562e5d6.s1.eu.hivemq.cloud"
port = 8883
username = os.getenv("MQTT_USERNAME")
password = os.getenv("MQTT_PASSWORD")
client_id = "zT4vYN89EU"
topic_in = "ACE/ACE/InBitC1"
topic_out = "ACE/ACE/OutBitD1"
topic_write = "ACE/ACE/WriteUI16Tag"

# Global flag to control thread running state
running = True

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to the input and output topics
        print(f"Subscribing to topics: {topic_in} and {topic_out}")
        client.subscribe(topic_in)
        client.subscribe(topic_out)
    else:
        print(f"Failed to connect, return code {rc}\n")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    received_message = msg.payload.decode()
    print(f"Received message: {received_message} from topic: {msg.topic}")

    # Save the message to the database
    save_message_to_db(msg.topic, received_message)

    # Save the message to the CSV file
    save_message_to_csv(msg.topic, received_message)

    # Check if the message is from the output topic and print the diode state
    if msg.topic == topic_out:
        print(f"Diode state changed: {received_message}")

# Callback when the client subscribes to a topic
def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Subscribed to topic with QoS: {granted_qos}")

# Enable detailed logging
def on_log(client, userdata, level, buf):
    print(f"Log: {buf}")

# Function to save messages to the database
def save_message_to_db(topic, message):
    conn = sqlite3.connect('mqtt_messages.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            topic TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        INSERT INTO messages (topic, message) VALUES (?, ?)
    ''', (topic, message))
    conn.commit()
    conn.close()

# Function to save messages to a CSV file
def save_message_to_csv(topic, message):
    file_exists = os.path.isfile('mqtt_messages.csv')
    with open('mqtt_messages.csv', mode='a', newline='') as csvfile:
        fieldnames = ['topic', 'message', 'timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({'topic': topic, 'message': message, 'timestamp': sqlite3.datetime.datetime.now()})

# Function to publish messages to the MQTT broker
def publish_message(client, topic, message):
    client.publish(topic, message)
    print(f"Published message: {message} to topic: {topic}")

# Function to handle user input for publishing messages
def user_input_publish():
    global running
    while running:
        try:
            user_input = input("Enter a message to publish to ACE/ACE/WriteUI16Tag: ")
            if not running:
                break
            publish_message(client, topic_write, user_input)
        except UnicodeDecodeError:
            print("Input interrupted, shutting down.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    global running
    print('Shutting down...')
    running = False
    client.disconnect()
    client.loop_stop()
    sys.exit(0)

# Register the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# Create an MQTT client instance
client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

# Set username and password
client.username_pw_set(username, password)

# Configure network encryption and authentication options
client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

# Attach the callback functions
client.on_connect = on_connect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_log = on_log

# Connect to the MQTT broker
client.connect(broker, port)

# Start a new thread for user input
input_thread = threading.Thread(target=user_input_publish)
input_thread.daemon = True
input_thread.start()

# Blocking loop to process network traffic, dispatch callbacks, and handle reconnecting
try:
    client.loop_forever()
except KeyboardInterrupt:
    signal_handler(signal.SIGINT, None)
