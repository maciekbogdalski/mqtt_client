import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

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

    # Check if the message is from the output topic and print the diode state
    if msg.topic == topic_out:
        print(f"Diode state changed: {received_message}")

# Callback when the client subscribes to a topic
def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Subscribed to topic with QoS: {granted_qos}")

# Enable detailed logging
def on_log(client, userdata, level, buf):
    print(f"Log: {buf}")

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

# Blocking loop to process network traffic, dispatch callbacks, and handle reconnecting
client.loop_forever()
