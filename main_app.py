import os
import sys
import subprocess
from dotenv import load_dotenv
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QMessageBox, QInputDialog

# Load environment variables
load_dotenv()

USER_USERNAME = os.getenv('USER_USERNAME')
USER_PASSWORD = os.getenv('USER_PASSWORD')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Script Runner")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Choose a script to run:")
        layout.addWidget(self.label)

        self.client_button = QPushButton("Run MQTT Client")
        self.client_button.clicked.connect(self.authenticate_and_run_client)
        layout.addWidget(self.client_button)

        self.retrieve_button = QPushButton("Run Data Retrieval")
        self.retrieve_button.clicked.connect(self.authenticate_and_run_retrieve)
        layout.addWidget(self.retrieve_button)

        self.decrypt_button = QPushButton("Run Decrypt CSV")
        self.decrypt_button.clicked.connect(self.authenticate_and_run_decrypt)
        layout.addWidget(self.decrypt_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit_app)
        layout.addWidget(self.exit_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.processes = []

    def run_client(self):
        process = subprocess.Popen(['python', 'client.py'])
        self.processes.append(process)

    def authenticate_and_run_client(self):
        username, password = self.prompt_for_credentials()
        if self.authenticate_user(username, password, role='user'):
            self.run_client()
        else:
            QMessageBox.warning(self, "Authentication Failed", "Invalid username or password")

    def authenticate_and_run_retrieve(self):
        username, password = self.prompt_for_credentials()
        if self.authenticate_user(username, password, role='admin'):
            process = subprocess.Popen(['python', 'retrieve_data.py'])
            self.processes.append(process)
        else:
            QMessageBox.warning(self, "Authentication Failed", "Admin access required")

    def authenticate_and_run_decrypt(self):
        username, password = self.prompt_for_credentials()
        if self.authenticate_user(username, password, role='admin'):
            process = subprocess.Popen(['python', 'decrypt_csv.py'])
            self.processes.append(process)
        else:
            QMessageBox.warning(self, "Authentication Failed", "Admin access required")

    def prompt_for_credentials(self):
        username, ok1 = QInputDialog.getText(self, "Authentication", "Enter username:", QLineEdit.Normal)
        password, ok2 = QInputDialog.getText(self, "Authentication", "Enter password:", QLineEdit.Password)
        if ok1 and ok2:
            return username, password
        return None, None

    def authenticate_user(self, username, password, role):
        if role == 'admin':
            return username == ADMIN_USERNAME and password == ADMIN_PASSWORD
        elif role == 'user':
            return (username == USER_USERNAME and password == USER_PASSWORD) or (username == ADMIN_USERNAME and password == ADMIN_PASSWORD)
        return False

    def exit_app(self):
        reply = QMessageBox.question(self, 'Exit Application',
                                     'Are you sure you want to exit?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            for process in self.processes:
                if process.poll() is None:  # Check if process is still running
                    process.terminate()
                    process.wait()  # Ensure the process has terminated
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
