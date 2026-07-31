import os
from ollama import Client
from pydantic import BaseModel

class WordList(BaseModel):
    items: list[str]


def load_from_file(filename):
    base = "./prompts"
    path = os.path.join(base, filename)

    print("Looking for:", path)

    if not os.path.isfile(path):
        raise IOError("File not found: %s" % path)

    with open(path, "r") as f:
        return f.read()

class WordlistGenerator():
    def __init__(self, tasks, tasks_lock):
        self.tasks = tasks
        self.tasks_lock = tasks_lock

    def generate_wordlist(self, prompt_file, task_id):
        try:
            system_prompt = load_from_file(prompt_file)
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
    
            response = ollama_client.chat(
                model=model,
                messages=messages,
                format=WordList.model_json_schema(),
                think=False
            )

            print(response)

            content = (
                response.message.content
                if hasattr(response, "message")
                else response["message"]["content"]
            )

            word_list = WordList.model_validate_json(content)

            

            result = {
                "task_id": task_id,
                "status": "complete",
                "details": word_list.items,
            }

            with self.tasks_lock:
                self.tasks[task_id] = result

        except Exception as exc:
            with self.tasks_lock:
                self.tasks[task_id] = {
                    "task_id": task_id,
                    "status": "error",
                    "error": str(exc),
                }