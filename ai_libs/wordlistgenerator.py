import os
from ollama import Client
from pydantic import BaseModel

model = "aratan/qwen3.5-uncensored:9b"
ollama_host = "http://localhost:11434"
ollama_client = Client(host=ollama_host)

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
        prompt_file = "wordlists.prompt.txt"
        system_prompt = load_from_file(prompt_file)
        self.messages=[{"role": "system", "content": system_prompt}]

    def generate_wordlist(self, task_id, score, score_lines):
        try:
            #if(len(self.messages) > 1):
            message = "Last score: "+str(score)+"\nscore breakdown:"+score_lines
            print(message)
            self.messages.append({"role": "user", "content": message})


            response = ollama_client.chat(
                model=model,
                messages=self.messages,
                format=WordList.model_json_schema(),
                think=False,
                options={
                    "repeat_penalty": 1.2
                }
            )

            #print(response)

            content = (
                response.message.content
                if hasattr(response, "message")
                else response["message"]["content"]
            )

            word_list = WordList.model_validate_json(content)

            self.messages.append({
                "role": "assistant",
                "content": content
            })


            

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