import os
from agno.models.openrouter.openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv()

model = OpenRouter(
    name="nvidia-super-120b-a12b",
    id="nemotron-3-super-120b-a12b:free",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="nvidia/nemotron-3-super-120b-a12b:free",
)
