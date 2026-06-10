import requests
import json

BASE_URL = "http://127.0.0.1:8000"


def show_items() -> None:
    response = requests.get(f"{BASE_URL}/items")
    response.raise_for_status()
    print("GET /items")
    print(json.dumps(response.json(), indent=2))
    print()


def add_item() -> None:
    payload = {
        "name": "AI Bitdefender Lab 7: Agents",
        "description": "This is inserted right now by a client.",
    }
    response = requests.post(f"{BASE_URL}/items", json=payload)
    response.raise_for_status()
    print("POST /items")
    print(json.dumps(response.json(), indent=2))
    print()


if __name__ == "__main__":
    show_items()
    add_item()
    show_items()

# python section_1/client.py