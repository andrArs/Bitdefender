from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Section 1 Demo")

DATA_FILE = Path(__file__).with_name("data.json")


class Item(BaseModel):
    id: int
    name: str
    description: str


class ItemCreate(BaseModel):
    name: str
    description: str


def load_items() -> list[Item]:
    if not DATA_FILE.exists():
        return []

    import json

    with DATA_FILE.open("r", encoding="utf-8") as file:
        raw_items = json.load(file)

    return [Item(**item) for item in raw_items]


def save_items(items: list[Item]) -> None:
    import json

    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump([item.dict() for item in items], file, indent=2)


if not DATA_FILE.exists():
    save_items(
        [
            Item(
                id=1,
                name="Graphs",
                description="Vertexes, Edges and Types of Graphs.",
            )
        ]
    )


@app.get("/items")
def get_items() -> dict:
    items = load_items()
    return {"items": items}


@app.post("/items")
def add_item(new_item: ItemCreate) -> dict:
    items = load_items()
    next_id = max((item.id for item in items), default=0) + 1

    item = Item(id=next_id, **new_item.dict())
    items.append(item)
    save_items(items)

    return {"message": "Item added successfully", "item": item}


@app.get("/")
def home() -> dict:
    return {
        "message": "Run this server, then use client.py to read and add items."
    }

# python -m uvicorn section_1.server:app --reload