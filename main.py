from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import json
import os

app = FastAPI()

TASKS_FILE = "tasks.json"
SUMMARY_FILE = "summary.json"

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as file:
            return json.load(file)
    return {day: [] for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}

def load_summary():
    if os.path.exists(SUMMARY_FILE):
        with open(SUMMARY_FILE, "r") as file:
            return json.load(file)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as file:
        json.dump(tasks, file)

def save_summary(summary):
    with open(SUMMARY_FILE, "w") as file:
        json.dump(summary, file)

class Task(BaseModel):
    title: str
    description: str

class CompletedTask(BaseModel):
    title: str
    description: str
    completed_at: str

tasks_db = load_tasks()
summary_db = load_summary()

@app.get("/tasks/{day}")
def get_tasks(day: str):
    return tasks_db.get(day, [])

@app.post("/tasks/{day}")
def add_task(day: str, task: Task):
    tasks_db[day].append(task.dict())
    save_tasks(tasks_db)
    return {"message": "Task added successfully"}

@app.delete("/tasks/{day}/{task_title}")
def delete_task(day: str, task_title: str):
    if day in tasks_db:
        tasks_db[day] = [task for task in tasks_db[day] if task["title"] != task_title]
        save_tasks(tasks_db)
        return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.post("/summary")
def add_to_summary(task: CompletedTask):
    summary_db.append(task.dict())
    save_summary(summary_db)
    return {"message": "Task added to summary"}

@app.get("/summary")
def get_summary():
    return summary_db

@app.delete("/summary")
def reset_summary():
    summary_db.clear()
    save_summary(summary_db)
    return {"message": "Summary reset successfully"}