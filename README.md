# JSM-Burp-Assist
Burp Local AI Assistant using Ollama

Requires that local Ollama is installed - https://ollama.com/download

Burp plugin uses Jython 2.7, API uses Python 3.11

Run API before using Burp plugin.

$ python3.11 api.py
 * Serving Flask app 'api'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.108:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!


Model or Ollama host can be passed to API:
$ python3.11 api.py --model=qwen3.5:latest --ollama-host=http://192.168.1.100:11434

# Open to job opportunities

I am currently looking for a new role. If you have an opening in AI or penetration testing, please feel free to reach out via LinkedIn: https://www.linkedin.com/in/michael-minchinton-2a5091273/
