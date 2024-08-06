import sqlite3
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLineEdit, QMessageBox
from datetime import datetime

class DataRetrievalWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MQTT Messages Database")
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.sql_input = QLineEdit()
        self.sql_input.setPlaceholderText("Enter SQL command")

        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self.execute_sql)

        self.today_button = QPushButton("Show Today's Records")
        self.today_button.clicked.connect(self.show_todays_records)

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)

        layout.addWidget(QLabel("SQL Command:"))
        layout.addWidget(self.sql_input)
        layout.addWidget(self.execute_button)
        layout.addWidget(self.today_button)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.result_box)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def execute_sql(self):
        command = self.sql_input.text()
        if command.strip():
            try:
                results = self.run_query(command)
                self.display_results(results)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Input Error", "Please enter a SQL command")

    def show_todays_records(self):
        today_date = datetime.now().strftime('%Y-%m-%d')
        query = f"SELECT * FROM messages WHERE DATE(timestamp) = '{today_date}'"
        try:
            results = self.run_query(query)
            self.display_results(results)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def run_query(self, query):
        conn = sqlite3.connect('mqtt_messages.db')
        c = conn.cursor()
        c.execute(query)
        if query.strip().lower().startswith("select"):
            results = c.fetchall()
        else:
            conn.commit()
            results = [(f"Query executed successfully: {query}",)]
        conn.close()
        return results

    def display_results(self, results):
        self.result_box.clear()
        for row in results:
            self.result_box.append(", ".join(map(str, row)))

def main():
    app = QApplication(sys.argv)
    window = DataRetrievalWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
