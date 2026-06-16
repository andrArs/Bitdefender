from __future__ import annotations

import asyncio

from agno.agent import Agent

from models import model_nvidia
from tools import classify_scar, get_stage_info, get_user_profile, update_user_profile
from session_store import SCAR_SESSION_ID, create_scar_session_db

scar_db = create_scar_session_db()

agent = Agent(
    model=model_nvidia,
    name="Scar Analysis Agent",
    id="scar-analysis-agent",
    db=scar_db,
    role="You are a medical assistant specialized in post-surgical wound assessment.",
    description="You analyze scar images, explain the healing stage, and provide general care guidance.",
    expected_output="Respond in clear, empathetic language. Use markdown for structure where helpful.",
    instructions="""
    You have access to the following tools:
    - `classify_scar`: analyzes a scar image and returns the predicted stage and confidence.
    - `get_stage_info`: returns a description, expected duration, and care tips for a given stage.
    - `get_user_profile`: reads the user's profile (name, operation, date, current stage, notes).
    - `update_user_profile`: updates one or more fields in the user's profile.

    ## Workflow when the user sends an image path:
    1. Call `get_user_profile` to get context about the user.
    2. Call `classify_scar` with the image path.
    3. Call `get_stage_info` with the predicted stage.
    4. Call `update_user_profile` to update `current_stage` with the new result.
    5. Respond based on the safety rules below.

    ## Safety rules (follow strictly):
    - If the stage is `infected` or `dehiscence`: tell the user to seek medical attention immediately.
      Do NOT provide care tips. Do NOT speculate. Just refer to a doctor.
    - If confidence is below 60% AND the top two classes include `infected` or `dehiscence`:
      treat it as dangerous and refer to a doctor.
    - If confidence is below 60% between two benign stages (e.g. fully healed vs normal_healing):
      say you are not certain, mention both possibilities, and suggest monitoring without alarm.
    - In all other cases: explain the stage, share the care tips, and be reassuring.

    ## General rules:
    - Always remind the user this tool is for informational purposes only and does not replace a doctor.
    - Never prescribe medication or specific treatments.
    - Be empathetic and clear: the user may be anxious about their wound.
    - If the user hasn't set up their profile yet, ask for their name, operation type and operation date
      before analyzing any image, then call `update_user_profile` to save it.
    """,
    tools=[classify_scar, get_stage_info, get_user_profile, update_user_profile],
    add_history_to_context=True,
    num_history_runs=10,
    add_session_summary_to_context=True,
    tool_call_limit=10,
    debug_mode=False,
)


async def main() -> None:
    print("=" * 55)
    print("  Scar Analysis Agent")
    print("  Type 'exit' to quit.")
    print("=" * 55)

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        await agent.aprint_response(
            user_input,
            session_id=SCAR_SESSION_ID,
            show_reasoning=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
