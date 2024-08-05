import sqlite3
import argparse

def retrieve_data(topic=None):
    conn = sqlite3.connect('mqtt_messages.db')
    c = conn.cursor()
    if topic:
        c.execute("SELECT * FROM messages WHERE topic=?", (topic,))
    else:
        c.execute("SELECT * FROM messages")
    rows = c.fetchall()
    for row in rows:
        print(row)
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve data from the MQTT messages database.')
    parser.add_argument('--topic', type=str, help='The topic to filter messages by.')
    args = parser.parse_args()
    retrieve_data(args.topic)
