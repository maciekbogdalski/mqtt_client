import os
import paho.mqtt.client as mqtt
import sqlite3
import csv
from dotenv import load_dotenv
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import signal
import sys
from datetime import datetime

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

# Function to log messages in the GUI
def log_message(message):
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, message + '\n')
    log_box.config(state=tk.DISABLED)
    log_box.yview(tk.END)
    print(message)  # Also print to console for easier debugging

# Function to update the state display
def update_state_display(topic, message):
    if topic == "ACE/ACE/InBitC1":
        in_state_label.config(text=f"Current In State: {message}")
    elif topic == "ACE/ACE/OutBitD1":
        out_state_label.config(text=f"Current Out State: {message}")
    elif topic == "ACE/ACE/WriteUI16Tag":
        if message != "0":
            write_state_label.config(text=f"Current Write State: {message}")

# Function to save messages to the database
def save_message_to_db(topic, message):
    try:
        conn = sqlite3.connect('mqtt_messages.db')
        c = conn.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                topic TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            INSERT INTO messages (topic, message, timestamp) VALUES (?, ?, ?)
        ''', (topic, message, current_time))
        conn.commit()
        conn.close()
        log_message(f"Saved message to DB: {message} from topic: {topic}")
    except Exception as e:
        log_message(f"Error saving to DB: {e}")

# Function to save messages to a CSV file
def save_message_to_csv(topic, message):
    try:
        file_exists = os.path.isfile('mqtt_messages.csv')
        with open('mqtt_messages.csv', mode='a', newline='') as csvfile:
            fieldnames = ['topic', 'message', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow({'topic': topic, 'message': message, 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        log_message(f"Saved message to CSV: {message} from topic: {topic}")
    except Exception as e:
        log_message(f"Error saving to CSV: {e}")

# Function to publish messages to the MQTT broker
def publish_message(client, topic, message, retain=False):
    client.publish(topic, message, retain=retain)
    log_message(f"Published message: {message} to topic: {topic}")
    if topic == "ACE/ACE/WriteUI16Tag":
        update_state_display(topic, message)
        save_message_to_db(topic, message)
        save_message_to_csv(topic, message)

# Callback when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log_message("Connected to MQTT Broker!")
        # Subscribe to all topics
        client.subscribe(wildcard_topic)
    else:
        log_message(f"Failed to connect, return code {rc}\n")

# Callback when a message is received from the broker
def on_message(client, userdata, msg):
    received_message = msg.payload.decode()
    log_message(f"Received message: {received_message} from topic: {msg.topic}")

    # Only save the message if the state has changed
    if msg.topic not in last_states or last_states[msg.topic] != received_message:
        last_states[msg.topic] = received_message
        # Update the GUI with the latest state if it's a known topic
        update_state_display(msg.topic, received_message)
        # Save the message to the database
        save_message_to_db(msg.topic, received_message)
        # Save the message to the CSV file
        save_message_to_csv(msg.topic, received_message)

# Callback when the client subscribes to a topic
def on_subscribe(client, userdata, mid, granted_qos):
    log_message(f"Subscribed to topic with QoS: {granted_qos}")

# Enable detailed logging
def on_log(client, userdata, level, buf):
    log_message(f"Log: {buf}")

# Function to handle user input for publishing messages
def publish_input_message():
    topic = topic_entry.get()
    message = message_entry.get()
    if topic and message:
        publish_message(client, topic, message, retain=True)
        message_entry.delete(0, tk.END)

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    global running
    log_message('Gracefully shutting down...')
    running = False
    client.disconnect()
    client.loop_stop()
    sys.exit(0)

# Create an MQTT client instance
client = mqtt.Client(client_id=client_id)

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

# GUI setup
root = tk.Tk()
root.title("MQTT Client")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

# Frame for state display
state_frame = tk.Frame(frame)
state_frame.pack(pady=10)

in_state_label = tk.Label(state_frame, text="Current In State: N/A", font=("Helvetica", 12))
in_state_label.pack(side=tk.LEFT, padx=5)

out_state_label = tk.Label(state_frame, text="Current Out State: N/A", font=("Helvetica", 12))
out_state_label.pack(side=tk.LEFT, padx=5)

write_state_label = tk.Label(state_frame, text="Current Write State: N/A", font=("Helvetica", 12))
write_state_label.pack(side=tk.LEFT, padx=5)

# Frame for log box
log_frame = tk.Frame(frame)
log_frame.pack(pady=10)

log_box = scrolledtext.ScrolledText(log_frame, width=50, height=20, state=tk.DISABLED)
log_box.pack()

# Frame for input
input_frame = tk.Frame(frame)
input_frame.pack(pady=10)

topic_label = tk.Label(input_frame, text="Enter topic:", font=("Helvetica", 12))
topic_label.pack(side=tk.LEFT, padx=5)

topic_entry = tk.Entry(input_frame, width=30)
topic_entry.pack(side=tk.LEFT, padx=5)

message_label = tk.Label(input_frame, text="Enter message:", font=("Helvetica", 12))
message_label.pack(side=tk.LEFT, padx=5)

message_entry = tk.Entry(input_frame, width=30)
message_entry.pack(side=tk.LEFT, padx=5)

publish_button = tk.Button(input_frame, text="Publish", command=publish_input_message)
publish_button.pack(side=tk.LEFT, padx=5)

def on_closing():
    global running
    if messagebox.askokcancel("Quit", "Do you want to quit?"):
        running = False
        client.disconnect()
        client.loop_stop()
        root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start a new thread for the MQTT client loop
mqtt_thread = threading.Thread(target=client.loop_forever)
mqtt_thread.daemon = True
mqtt_thread.start()

# Run the Tkinter event loop
root.mainloop()
