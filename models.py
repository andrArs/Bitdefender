import os
from agno.models.openrouter.openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv()

model_nvidia = OpenRouter(
    name="nvidia-super-120b-a12b",
    id="nemotron-3-super-120b-a12b:free",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="nvidia/nemotron-3-super-120b-a12b:free",
)

model_hermes = OpenRouter(
    name="hermes-3-llama-3.1-405b",
    id="hermes-3-llama-3.1-405b",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="nousresearch/hermes-3-llama-3.1-405b:free",
)

model_gemma = OpenRouter(
    name="gemma-4-31b-it",
    id="gemma-4-31b-it",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="google/gemma-4-31b-it:free",
)
