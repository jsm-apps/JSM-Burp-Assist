# app.py (needs to be run using python 3.11 or higher)

import threading
import time
import uuid

from flask import Flask, jsonify, request, redirect, url_for
from ollama import Client
import requests
import os
import json

from pydantic import BaseModel

from ai_libs.wordlistgenerator import WordlistGenerator
from ai_libs.aiutil import AIUtil

model = "aratan/qwen3.5-uncensored:9b"
ollama_host = "http://localhost:11434"
ollama_client = Client(host=ollama_host)

aiutil = AIUtil()

app = Flask(__name__)

# In-memory task storage.
# Replace this with Redis or a database for production use.
tasks = {}
tasks_lock = threading.Lock()
generator = WordlistGenerator(tasks, tasks_lock)


def process_ai_task(prompt_file, task_id, url, raw_response):
    """
    Simulate a task that takes 10 seconds.
    """
    try:
        #time.sleep(10)

        http_response = raw_response
        summary = aiutil.create_summary(prompt_file, url, http_response)

        result = {
            "task_id": task_id,
            "status": "complete",
            "title": "Example title",
            "url": url,
            "details": summary,
        }

        with tasks_lock:
            tasks[task_id] = result

    except Exception as exc:
        with tasks_lock:
            tasks[task_id] = {
                "task_id": task_id,
                "status": "error",
                "error": str(exc),
            }





@app.route("/ai/wordlist", methods=["GET", "POST"])
def get_wordlist():
    data = request.get_json(silent=True)
    
    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    score = data.get("score")
    score_lines = data.get("score_lines")


    task_id = str(uuid.uuid4())
    
    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "status": "pending"
        }

    worker = threading.Thread(
        target=generator.generate_wordlist,
        args=(task_id, score, score_lines,),
        daemon=True,
    )
    worker.start()

    return jsonify({
            "task_id": task_id,
            "status": "pending",
        }), 202
        
    #return redirect(url_for("get_task", task_id=task_id))



@app.route("/ai/techdetect", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    url = data.get("url")

    raw_response = data.get("raw_response")

    if not url or not isinstance(url, str):
        return jsonify({
            "error": "A valid URL string is required."
        }), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({
            "error": "URL must start with http:// or https://."
        }), 400

    task_id = str(uuid.uuid4())

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "url": url,
        }

    worker = threading.Thread(
        target=process_ai_task,
        args=("techdetect.prompt.txt", task_id, url, raw_response),
        daemon=True,
    )
    worker.start()

    return jsonify({
        "task_id": task_id,
        "status": "pending",
    }), 202


@app.route("/ai/xssdetect", methods=["POST"])
def create_xss_task():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    url = data.get("url")

    raw_response = data.get("raw_response")

    if not url or not isinstance(url, str):
        return jsonify({
            "error": "A valid URL string is required."
        }), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({
            "error": "URL must start with http:// or https://."
        }), 400

    task_id = str(uuid.uuid4())

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "url": url,
        }

    worker = threading.Thread(
        target=process_ai_task,
        args=("xssdetect.prompt.txt", task_id, url, raw_response),
        daemon=True,
    )
    worker.start()

    return jsonify({
        "task_id": task_id,
        "status": "pending",
    }), 202



@app.route("/ai/ask-question", methods=["POST"])
def create_question_task():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Request body must contain JSON."
        }), 400

    url = data.get("url")

    raw_response = data.get("raw_response")
    question = data.get("question")

    if not url or not isinstance(url, str):
        return jsonify({
            "error": "A valid URL string is required."
        }), 400

    if not url.startswith(("http://", "https://")):
        return jsonify({
            "error": "URL must start with http:// or https://."
        }), 400

    # write question to prompts/question.prompt.txt
    with open("prompts/question.prompt.txt", "w", encoding="utf-8") as f:
        f.write(question)

    task_id = str(uuid.uuid4())

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "url": url,
        }

    worker = threading.Thread(
        target=process_ai_task,
        args=("question.prompt.txt", task_id, url, raw_response),
        daemon=True,
    )
    worker.start()

    return jsonify({
        "task_id": task_id,
        "status": "pending",
    }), 202


@app.route("/task/<task_id>", methods=["GET"])
def get_task(task_id):
    with tasks_lock:
        task = tasks.get(task_id)

    if task is None:
        return jsonify({
            "error": "Task not found."
        }), 404

    return jsonify(task), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        threaded=True,
    )