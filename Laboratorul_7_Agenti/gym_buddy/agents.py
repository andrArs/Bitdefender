from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from agno.agent import Agent
from agno.team import Team

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from gym_buddy.models import model
from gym_buddy.mcp_tools import NUTRITION_TOOLS, WORKOUT_TOOLS
from gym_buddy.session_store import GYM_SESSION_ID, create_gym_session_db

gym_db = create_gym_session_db()

nutrition_agent = Agent(
    model=model,
    name="Nutrition Agent",
    id="nutrition-agent",
    role="You are a personal nutrition coach.",
    description="You help users with meal plans, diet advice, and nutrition information.",
    expected_output="Respond in markdown with clear sections, tables where useful.",
    instructions="""
    You have access to the following tools:
    - `get_user_profile` to read the user's profile (weight, goal, fitness level).
    - `update_user_profile` to update weight or goal.
    - `save_meal_plan` to save a meal plan as a markdown file.
    - `web_search` to find nutrition information, recipes, or diet advice.

    ALWAYS call `get_user_profile` as the FIRST action before doing anything else.
    Use the profile data to personalize every response, never ask the user for info already in the profile.
    ALWAYS call `save_meal_plan` as the LAST action after generating a plan. Never skip this step.
    """,
    tools=[NUTRITION_TOOLS],
    add_history_to_context=True,
    num_history_runs=10,
    tool_call_limit=10,
    debug_mode=True,
)

workout_agent = Agent(
    model=model,
    name="Workout Agent",
    id="workout-agent",
    role="You are a personal fitness coach and trainer.",
    description="You help users with workout plans, exercise tips, and progress tracking.",
    expected_output="Respond in markdown with clear sections, tables where useful.",
    instructions="""
    You have access to the following tools:
    - `get_user_profile_workout` to read the user's profile (weight, goal, fitness level).
    - `save_workout_plan` to save a workout plan as a markdown file.
    - `log_progress` to log weight and exercise performance (kg, reps, sets).
    - `read_progress` to read the full progress history and compare over time.
    - `get_exercise_tips` to find correct form, common mistakes, and variations for an exercise.
    - `web_search_workout` to find fitness information or training programs.

    ALWAYS call `get_user_profile_workout` as the FIRST action before doing anything else.
    Use the profile data to personalize every response, never ask the user for info already in the profile.
    When the user says they don't feel well, suggest lighter alternatives using get_exercise_tips.
    ALWAYS call `save_workout_plan` as the LAST action after generating a plan. Never skip this step.
    """,
    tools=[WORKOUT_TOOLS],
    add_history_to_context=True,
    num_history_runs=10,
    tool_call_limit=10,
    debug_mode=True,
)

gym_team = Team(
    model=model,
    name="Gym Buddy Team",
    members=[nutrition_agent, workout_agent],
    db=gym_db,
    session_id=GYM_SESSION_ID,
    cache_session=True,
    determine_input_for_members=True,
    role="You are a personal gym buddy, a coach that covers both training and nutrition.",
    description="A team of agents that help with fitness and nutrition goals.",
    expected_output="Respond in markdown with clear sections, tables where useful.",
    instructions="""
    You have 2 agents:
    - Nutrition Agent: meal plans, diet advice, calories, macros.
    - Workout Agent: training plans, exercise tips, progress tracking.

    IMPORTANT: The user's profile is already stored, NEVER ask the user for info that's in the profile.
    NEVER generate plans yourself, ALWAYS delegate to the appropriate agent.
    Delegate immediately without asking clarifying questions first.

    Route requests to the right agent. For complex requests (e.g. full weekly plan),
    use both agents and combine their responses.
    """,
    show_members_responses=True,
    share_member_interactions=True,
    add_history_to_context=True,
    enable_session_summaries=True,
    store_events=True,
    store_member_responses=True,
    num_history_runs=10,
    add_session_summary_to_context=True,
    tool_call_limit=10,
    debug_mode=True,
)


async def main() -> None:
    await workout_agent.aprint_response(
        "Create a complete personalized workout plan for 4 days a week and save it.",
        show_reasoning=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
