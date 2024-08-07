# MQTT Client with SQLite, InfluxDB, and Grafana Integration

## Overview

This project is an MQTT client application that receives messages from an MQTT broker, saves the messages to an SQLite database and InfluxDB, and visualizes the data in Grafana. The application includes encryption for data storage and offers a GUI for monitoring MQTT messages.

## Features

- Connects to an MQTT broker to subscribe and publish messages.
- Stores MQTT messages in an SQLite database with encryption.
- Stores MQTT messages in InfluxDB for real-time visualization.
- Provides a GUI to monitor MQTT messages and their states.
- Integration with Grafana for data visualization.
- RBAC (Role-Based Access Control) for running data retrieval scripts.

## Prerequisites

- Python 3.8+
- InfluxDB Cloud account (or a local InfluxDB instance)
- Grafana for data visualization

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/mqtt-client.git
    cd mqtt-client
    ```

2. **Install the required packages:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Create the environment variable files:**

    - **config.env:**

        Copy the example configuration file and fill in your details:

        ```sh
        cp config.env.example config.env
        ```

        Edit the `config.env` file with your details:

        ```plaintext
        MQTT_USERNAME=your_mqtt_username
        MQTT_PASSWORD=your_mqtt_password
        INFLUXDB_URL=https://your-influxdb-url
        INFLUXDB_TOKEN=your_influxdb_token
        INFLUXDB_ORG=your_organization_name
        INFLUXDB_BUCKET=your_bucket_name
        ```

    - **.env:**

        Copy the example environment file and fill in your details:

        ```sh
        cp .env.example .env
        ```

        Edit the `.env` file with your details:

        ```plaintext
        USER_USERNAME=user
        USER_PASSWORD=user_password
        ADMIN_USERNAME=admin
        ADMIN_PASSWORD=admin_password
        ```

4. **Generate an encryption key:**

    Run the following script to generate an encryption key:

    ```sh
    python generate_key.py
    ```

    This will create an `encryption_key.key` file in your project directory.

## Usage

### Running the Main Application with RBAC

1. **Running the main application:**

    ```sh
    python main_app.py
    ```

    This will start the main application that provides a GUI to run the MQTT client or data retrieval script based on the user's role.

### Generating an Executable

To generate an executable for the main application using `PyInstaller`, run the following command:

```sh
pyinstaller --onefile --distpath . --workpath . --specpath . main_app.py
