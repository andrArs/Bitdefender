"""MCP servers for the Gym Buddy project."""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from gym_buddy.tools import (
    get_user_profile as get_user_profile_local,
    update_user_profile as update_user_profile_local,
    save_meal_plan as save_meal_plan_local,
    save_workout_plan as save_workout_plan_local,
    log_progress as log_progress_local,
    read_progress as read_progress_local,
    get_exercise_tips as get_exercise_tips_local,
    web_search as web_search_local,
)


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


logger = setup_logger("gym_buddy")

nutrition_mcp = FastMCP("Nutrition Server", stateless_http=True)
workout_mcp = FastMCP("Workout Server", stateless_http=True)

@nutrition_mcp.tool()
async def get_user_profile() -> dict:
    """Read the user's profile (name, age, weight, height, goal, fitness level).

    Always call this first before generating any plan so the response is personalized.
    """
    logger.info("nutrition.get_user_profile()")
    return get_user_profile_local()


@nutrition_mcp.tool()
async def update_user_profile(updates: dict) -> dict:
    """Update one or more fields in the user profile.

    Use this when the user reports a new weight, changes their goal, or updates
    any profile field. Pass only the fields that changed.
    """
    logger.info("nutrition.update_user_profile(%s)", updates)
    return update_user_profile_local(updates)


@nutrition_mcp.tool()
async def save_meal_plan(title: str, body: str) -> dict:
    """Save a meal plan as a Markdown file.

    Always call this after generating a meal plan. `title` is a short name
    like 'Weekly Meal Plan – June 2026'. `body` is the full markdown content.
    """
    logger.info("nutrition.save_meal_plan(%s)", title)
    return save_meal_plan_local(title, body)


@nutrition_mcp.tool()
async def web_search(query: str, max_results: int = 5) -> dict:
    """Search the web for nutrition information, recipes, or diet advice.

    Use this for fresh information like 'high protein breakfast ideas' or
    'calories in chicken breast'. Pass a short focused query.
    """
    logger.info("nutrition.web_search(%s)", query)
    return web_search_local(query, max_results)


@workout_mcp.tool()
async def get_user_profile_workout() -> dict:
    """Read the user's profile (name, age, weight, height, goal, fitness level).

    Always call this first before generating any plan so the response is personalized.
    """
    logger.info("workout.get_user_profile()")
    return get_user_profile_local()


@workout_mcp.tool()
async def save_workout_plan(title: str, body: str) -> dict:
    """Save a workout plan as a Markdown file.

    Always call this after generating a workout plan. `title` is a short name
    like '4-Day Muscle Building Plan'. `body` is the full markdown content.
    """
    logger.info("workout.save_workout_plan(%s)", title)
    return save_workout_plan_local(title, body)


@workout_mcp.tool()
async def log_progress(
    weight_kg: float | None = None,
    exercises: dict | None = None,
    notes: str = "",
) -> dict:
    """Log today's progress entry.

    Use this when the user reports their current weight or exercise performance.
    `exercises` should be a dict like:
    {"bench_press": {"kg": 60, "reps": 10, "sets": 3}}
    """
    logger.info("workout.log_progress(weight=%s)", weight_kg)
    return log_progress_local(weight_kg, exercises, notes)


@workout_mcp.tool()
async def read_progress() -> dict:
    """Read all progress entries sorted by date.

    Use this to compare performance over time or show the user their history.
    """
    logger.info("workout.read_progress()")
    return read_progress_local()


@workout_mcp.tool()
async def get_exercise_tips(exercise_name: str) -> dict:
    """Search the web for correct form, common mistakes, and variations for an exercise.

    Use this when the user asks how to do an exercise correctly, or when they
    say they don't feel well and need lighter alternatives.
    """
    logger.info("workout.get_exercise_tips(%s)", exercise_name)
    return get_exercise_tips_local(exercise_name)


@workout_mcp.tool()
async def web_search_workout(query: str, max_results: int = 5) -> dict:
    """Search the web for fitness information or training programs.

    Use this for fresh information like 'beginner PPL program' or
    'how many sets per week for hypertrophy'.
    """
    logger.info("workout.web_search(%s)", query)
    return web_search_local(query, max_results)


nutrition_app = nutrition_mcp.streamable_http_app()
workout_app = workout_mcp.streamable_http_app()


def combined_lifespan(proxy_apps):
    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with contextlib.AsyncExitStack() as stack:
            for proxy_app in proxy_apps:
                await stack.enter_async_context(proxy_app.router.lifespan_context(app))
            yield
    return lifespan


app = FastAPI(debug=True, lifespan=combined_lifespan([nutrition_app, workout_app]))
app.mount("/mcp/nutrition", nutrition_app)
app.mount("/mcp/workout", workout_app)


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8300)


if __name__ == "__main__":
    main()
