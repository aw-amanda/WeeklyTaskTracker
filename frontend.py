import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget, QDialog,
    QLineEdit, QCheckBox, QMessageBox, QHBoxLayout, QListWidget, QListWidgetItem, QDateEdit, QTimeEdit
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QIcon


class TaskDialog(QDialog):
    def __init__(self, day, parent=None):
        super().__init__(parent)
        self.day = day
        self.setWindowTitle(f"Add Task for {day}")
        self.layout = QVBoxLayout()

        self.title_input = QLineEdit(self)
        self.title_input.setPlaceholderText("Task Title")
        self.layout.addWidget(self.title_input)

        self.description_input = QLineEdit(self)
        self.description_input.setPlaceholderText("Task Description")
        self.layout.addWidget(self.description_input)

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)
        self.layout.addWidget(self.ok_button)

        self.setLayout(self.layout)

    def get_task(self):
        return {
            "title": self.title_input.text(),
            "description": self.description_input.text()
        }

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weekly Task Tracker")
        self.setGeometry(100, 100, 1500, 300)
        self.setWindowIcon(QIcon("WeeklyTaskTrackerIcon.ico"))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.task_lists = {}

        self.setStyleSheet("""
            QWidget{ 
                background-color: #1f1e1f;
                color: #bb9cf2;
            }
            QLabel{
                font-size: 20px;
                font-family: Arial;
                color:#bb9cf2;
                qproperty-alignment: AlignCenter;
                padding: 20px;
            }
            QPushButton{
                font-size: 15px;
                font-weight: 400;
                color: #1f1e1f;
                background-color: #bb9cf2;
                padding: 5px 10px;
                border: 1px solid #1f1e1f;
                border-radius: 10px;
                margin: 5px;            
            }
            QListWidget{
                background-color: #1f1e1f;
                border: 1px solid #bb9cf2;
                border-radius: 10px;
                padding: 10px;
            }
            QListWidgetItem{
                font-size: 5px;
                font-family: Arial;
                color: #bb9cf2;
                margin: 1px;
            }
            TaskDialog{
                background-color: #1f1e1f;
            }
            QCheckBox {
                spacing: 2px;
            }
            QCheckBox::indicator {
                width: 8px;
                height: 8px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ffffff;
                border: 1px solid #ffffff;
                border-radius: 5px;
            }
""")

        for day in self.days:
            day_widget = QWidget()
            day_layout = QVBoxLayout()
            day_widget.setLayout(day_layout)

            day_label = QLabel(day, self)
            day_layout.addWidget(day_label)

            add_button = QPushButton("+", self)
            add_button.clicked.connect(lambda _, d=day: self.add_task(d))
            day_layout.addWidget(add_button)

            task_list = QListWidget(self)
            self.task_lists[day] = task_list
            day_layout.addWidget(task_list)

            self.layout.addWidget(day_widget)

        self.summary_button = QPushButton("View Summary", self)
        self.summary_button.clicked.connect(self.view_summary)
        self.layout.addWidget(self.summary_button)

        self.load_tasks()

    def add_task(self, day):
        dialog = TaskDialog(day, self)
        if dialog.exec_():
            task = dialog.get_task()
            if task["title"]:
                self.add_task_to_list(day, task)
                requests.post(f"http://127.0.0.1:8000/tasks/{day}", json=task)

    def add_task_to_list(self, day, task):
        task_widget = QWidget()
        task_layout = QHBoxLayout()
        task_widget.setLayout(task_layout)

        checkbox = QCheckBox()
        task_layout.addWidget(checkbox)

        task_label = QLabel(f"{task['title']}: {task['description']}")
        task_layout.addWidget(task_label)

        list_item = QListWidgetItem(self.task_lists[day])
        list_item.setSizeHint(task_widget.sizeHint())
        self.task_lists[day].addItem(list_item)
        self.task_lists[day].setItemWidget(list_item, task_widget)

        checkbox.stateChanged.connect(lambda state, d=day, item=list_item: self.task_completed(state, d, item, task))

    def task_completed(self, state, day, list_item, task):
        if state == Qt.Checked:
            # Remove the task from the main list
            self.task_lists[day].takeItem(self.task_lists[day].row(list_item))

            # Delete the task from the backend
            requests.delete(f"http://127.0.0.1:8000/tasks/{day}/{task['title']}")

            # Add the task to the summary
            completed_task = {
                **task,
                "completed_at": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm ap")
            }
            requests.post("http://127.0.0.1:8000/summary", json=completed_task)

    def load_tasks(self):
        for day in self.days:
            tasks = requests.get(f"http://127.0.0.1:8000/tasks/{day}").json()
            for task in tasks:
                self.add_task_to_list(day, task)

    def view_summary(self):
        summary_dialog = QDialog(self)
        summary_dialog.setWindowTitle("Task Summary")
        summary_layout = QVBoxLayout()

        summary_list = QListWidget(summary_dialog)
        summary = requests.get("http://127.0.0.1:8000/summary").json()
        for task in summary:
            item = QListWidgetItem(f"{task['completed_at']}: {task['title']} - {task['description']}")
            summary_list.addItem(item)

        summary_layout.addWidget(summary_list)

        reset_button = QPushButton("RESET", summary_dialog)
        reset_button.setStyleSheet("background-color: red; color: white;")
        reset_button.clicked.connect(self.reset_summary)
        summary_layout.addWidget(reset_button)

        summary_dialog.setLayout(summary_layout)
        summary_dialog.exec_()

    def reset_summary(self):
        confirm = QMessageBox.question(self, "Reset Summary", "Are you sure you want to reset the summary?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            requests.delete("http://127.0.0.1:8000/summary")
            QMessageBox.information(self, "Summary Reset", "The summary has been reset.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())