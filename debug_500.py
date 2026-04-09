import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test():
    req = client.get("/f/mWXmFk0b7B8")
    print(f"Status: {req.status_code}")
    print(req.text)

if __name__ == "__main__":
    test()
