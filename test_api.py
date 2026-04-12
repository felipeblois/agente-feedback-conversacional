import urllib.request
import json
import os
from app.core.config import get_settings

settings = get_settings()
key = settings.gemini_api_key

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"

data = {
    "contents": [{"parts":[{"text": "Hello"}]}]
}
req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as f:
        print(f.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Erro HTTP: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Erro: {e}")
