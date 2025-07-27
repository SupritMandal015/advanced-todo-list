import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QComboBox, QListWidget,
    QListWidgetItem, QMessageBox, QDateEdit, QCheckBox
)
from PyQt5.QtCore import QDate, QTimer

TASKS_FILE = "tasks.json"

class ToDoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced To-Do List")
        self.resize(600, 500)
        self.tasks = self.load_tasks()
        self.init_ui()
        self.auto_refresh()

    def init_ui(self):
        layout = QVBoxLayout()

        # Input Section
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task title")

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        self.priority_input = QComboBox()
        self.priority_input.addItems(["Low", "Medium", "High"])

        self.pin_checkbox = QCheckBox("📌 Pin Task")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(QLabel("Due:"))
        input_layout.addWidget(self.date_input)
        input_layout.addWidget(QLabel("Priority:"))
        input_layout.addWidget(self.priority_input)
        input_layout.addWidget(self.pin_checkbox)

        self.add_button = QPushButton("Add Task")
        self.add_button.clicked.connect(self.add_task)

        # Task List
        self.task_list = QListWidget()
        self.task_list.itemDoubleClicked.connect(self.toggle_done)

        self.delete_button = QPushButton("Delete Task")
        self.delete_button.clicked.connect(self.delete_task)

        # Filter Section
        filter_layout = QHBoxLayout()

        self.filter_priority = QComboBox()
        self.filter_priority.addItems(["All", "Low", "Medium", "High"])
        self.filter_priority.currentTextChanged.connect(self.refresh_list)

        self.filter_date = QDateEdit()
        self.filter_date.setCalendarPopup(True)
        self.filter_date.setDate(QDate.currentDate())
        self.filter_date.dateChanged.connect(self.refresh_list)

        filter_layout.addWidget(QLabel("Filter Priority:"))
        filter_layout.addWidget(self.filter_priority)
        filter_layout.addWidget(QLabel("Due before/on:"))
        filter_layout.addWidget(self.filter_date)

        layout.addLayout(input_layout)
        layout.addWidget(self.add_button)
        layout.addLayout(filter_layout)
        layout.addWidget(self.task_list)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)
        self.refresh_list()

    def auto_refresh(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_list)
        self.timer.start(5000)  # Refresh every 5 seconds

    def load_tasks(self):
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "r") as f:
                tasks = json.load(f)
            # Ensure all required keys exist in old tasks
            for task in tasks:
                task.setdefault("due_date", QDate.currentDate().toString("yyyy-MM-dd"))
                task.setdefault("priority", "Low")
                task.setdefault("pinned", False)
                task.setdefault("done", False)
            return tasks
        return []

    def save_tasks(self):
        with open(TASKS_FILE, "w") as f:
            json.dump(self.tasks, f, indent=4)

    def refresh_list(self):
        self.task_list.clear()
        priority_filter = self.filter_priority.currentText()
        date_filter = self.filter_date.date().toPyDate()

        # Sort by pinned first, then due date
        filtered_tasks = sorted(self.tasks, key=lambda x: (not x.get("pinned", False), x["due_date"]))

        for task in filtered_tasks:
            task_due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
            if (priority_filter != "All" and task["priority"] != priority_filter) or (task_due_date > date_filter):
                continue

            status = "✔" if task["done"] else "✘"
            pin = "📌" if task.get("pinned", False) else ""
            item = QListWidgetItem(f"{pin}[{status}] {task['title']} | Due: {task['due_date']} | Priority: {task['priority']}")
            self.task_list.addItem(item)

    def add_task(self):
        title = self.task_input.text().strip()
        due_date = self.date_input.date().toString("yyyy-MM-dd")
        priority = self.priority_input.currentText()
        pinned = self.pin_checkbox.isChecked()

        if not title:
            QMessageBox.warning(self, "Error", "Task title cannot be empty.")
            return

        self.tasks.append({
            "title": title,
            "due_date": due_date,
            "priority": priority,
            "pinned": pinned,
            "done": False
        })

        self.task_input.clear()
        self.pin_checkbox.setChecked(False)
        self.save_tasks()
        self.refresh_list()

    def toggle_done(self, item):
        index = self.task_list.row(item)
        visible_items = self.get_visible_task_indices()

        if index < len(visible_items):
            real_index = visible_items[index]
            self.tasks[real_index]["done"] = not self.tasks[real_index]["done"]
            self.save_tasks()
            self.refresh_list()

    def delete_task(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return

        visible_items = self.get_visible_task_indices()

        for item in selected_items:
            index = self.task_list.row(item)
            if index < len(visible_items):
                real_index = visible_items[index]
                self.tasks.pop(real_index)

        self.save_tasks()
        self.refresh_list()

    def get_visible_task_indices(self):
        """Returns the indices of visible tasks after filters and sort."""
        priority_filter = self.filter_priority.currentText()
        date_filter = self.filter_date.date().toPyDate()
        visible = []

        for i, task in enumerate(sorted(self.tasks, key=lambda x: (not x.get("pinned", False), x["due_date"]))):
            task_due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
            if (priority_filter != "All" and task["priority"] != priority_filter) or (task_due_date > date_filter):
                continue
            visible.append(i)
        return visible


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToDoApp()
    window.show()
    sys.exit(app.exec_())
