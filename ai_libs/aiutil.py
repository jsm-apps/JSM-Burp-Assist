import os
from ollama import Client

class AIUtil():
    def __init__(self, model, ollama_host):
        self.model = model
        self.ollama_host = ollama_host
        self.ollama_client = Client(host=self.ollama_host)
    
    def load_from_file(self, filename):
        base = "./prompts"
        path = os.path.join(base, filename)

        print("Looking for:", path)

        if not os.path.isfile(path):
            raise IOError("File not found: %s" % path)

        with open(path, "r") as f:
            return f.read()

    def create_summary(self, system_prompt_file, url, stringcontent):
        if stringcontent is None:
            raise ValueError("stringcontent is required")

        stringcontent = str(stringcontent).strip()

        if not stringcontent:
            raise ValueError("stringcontent cannot be empty")

        system_prompt = self.load_from_file(system_prompt_file)

        prompt = (
            "URL: {}\n"
            "HTTP Response:\n"
            "{}"
        ).format(url, stringcontent)

        full_prompt = system_prompt+"\n"+prompt
        print(full_prompt)

        try:
            response = self.ollama_client.generate(
                model=self.model,
                prompt=full_prompt
            )

            # Support both object-style and dictionary-style responses.
            if hasattr(response, "response"):
                summary = response.response
            else:
                summary = response.get("response")

            if not summary:
                raise RuntimeError(
                    "Ollama returned an empty summary"
                )

            return summary.strip()

        except Exception as exc:
            raise RuntimeError(
                "Failed to create summary: {}".format(exc)
            )