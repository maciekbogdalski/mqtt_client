import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QMessageBox

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Script Runner")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Choose a script to run:")
        layout.addWidget(self.label)

        self.client_button = QPushButton("Run MQTT Client")
        self.client_button.clicked.connect(self.run_client)
        layout.addWidget(self.client_button)

        self.retrieve_button = QPushButton("Run Data Retrieval")
        self.retrieve_button.clicked.connect(self.run_retrieve)
        layout.addWidget(self.retrieve_button)

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

    def run_retrieve(self):
        process = subprocess.Popen(['python', 'retrieve_data.py'])
        self.processes.append(process)

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