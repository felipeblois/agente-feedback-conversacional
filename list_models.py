import urllib.request
import json
from app.core.config import get_settings

settings = get_settings()
key = settings.gemini_api_key

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"

req = urllib.request.Request(url)

try:
    with urllib.request.urlopen(req) as f:
        data = json.loads(f.read().decode('utf-8'))
        print("Modelos disponíveis:")
        for m in data.get("models", []):
            print(m["name"])
except Exception as e:
    print(f"Erro: {e}")
