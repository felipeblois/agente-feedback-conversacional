import json
import urllib.request

from app.core.config import get_settings


settings = get_settings()
key = settings.gemini_api_key

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
req = urllib.request.Request(url)

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
        print("Modelos Gemini disponiveis:")
        for model in data.get("models", []):
            print(model["name"])
except Exception as exc:
    print(f"Erro: {exc}")
