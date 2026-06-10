import os
from agno.models.openrouter.openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv()
model_gemma_4_31b_it = OpenRouter(
    name="gemma-4-31b-it",
    id="gemma-4-31b-it",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="google/gemma-4-31b-it:free",
)

model_gemma_4_26b_a4b_it = OpenRouter(
    name="gemma-4-26b-a4b-it",
    id="gemma-4-26b-a4b-it",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="google/gemma-4-26b-a4b-it:free",
)

model_hermes_3_llama_3_1_405b = OpenRouter(
    name="hermes-3-llama-3.1-405b",
    id="hermes-3-llama-3.1-405b",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="nousresearch/hermes-3-llama-3.1-405b:free",
)

model_nvidia_nano_omni_30b_a3b_reasoning = OpenRouter(
    name="nvidia-nano-omni-30b-a3b-reasoning",
    id="nvidia-nano-omni-30b-a3b-reasoning",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
)

model_nvidia_super_120b_a12b = OpenRouter(
    name="nvidia-super-120b-a12b",
    id="nemotron-3-super-120b-a12b:free",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    models="nvidia/nemotron-3-super-120b-a12b:free",
)

# import os
# from dotenv import load_dotenv
# from agno.models.openrouter import OpenRouter

# load_dotenv()

# COMMON_CONFIG = {
#     "api_key": os.getenv("OPEN_ROUTER_API_KEY"),
#     "base_url": "https://openrouter.ai/api/v1",
#     "temperature": 0.2,
#     "max_tokens": 1024,
#     "request_params": {
#         "top_p": 0.9,
#         "frequency_penalty": 0.1,
#         "presence_penalty": 0.0,
#     },
# }

# FAST_MODEL = OpenRouter(
#     id="google/gemma-4-26b-a4b-it:free",
#     name="fast",
#     **COMMON_CONFIG,
# )

# BALANCED_MODEL = OpenRouter(
#     id="google/gemma-4-31b-it:free",
#     name="balanced",
#     **COMMON_CONFIG,
# )

# STRONG_MODEL = OpenRouter(
#     id="nousresearch/hermes-3-llama-3.1-405b:free",
#     name="strong",
#     **COMMON_CONFIG,
# )

# NVIDIA_MODEL = OpenRouter(
#     id="nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
#     name="nvidia",
#     **COMMON_CONFIG,
# )

# NIVIDIA_MODEL_2 = OpenRouter(
#     id="nvidia/nemotron-3-super-120b-a12b:free",
#     name="nvidia_2",
#     **COMMON_CONFIG,
# )