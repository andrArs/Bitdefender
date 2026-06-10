import asyncio
import sys
from pathlib import Path

from agno.team import Team
from agno.tools.reasoning import ReasoningTools

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from section_4.agent import college_buddy_agent, personal_assistant_agent
from section_3.models import model_nvidia_super_120b_a12b
from section_5.session_store import TEAM_SESSION_ID, create_team_session_db

team_db = create_team_session_db()

personal_assistant_team = Team(
    model=model_nvidia_super_120b_a12b,
    members=[personal_assistant_agent, college_buddy_agent], # ReasoningTools(add_instructions=True)
    db=team_db,
    session_id=TEAM_SESSION_ID,
    cache_session=True,
    determine_input_for_members=True,
    name="Personal Assistant Team",
    role="You are a helpful assistant that can help with personal related tasks.",
    description="A team of agents that can help with personal related tasks.",
    expected_output="The response should be in markdown format and pretty printed for the user to read. You can use dashes, tables, strings, everything that you consider to use.",
    instructions="""
    You have 2 agents under your command:
    - Personal Assistant Agent
    - College Buddy Agent

    1.) Personal Assistant Agent is responsible for handling personal related tasks.
    This agent can read the schedule of a user, get weather details, search things on web, and add an event to the calendar.
    
    2.) College Buddy Agent is responsible for handling college related tasks.
    This agent can search for something in a directory with notes, search different things in a pdf, and write and save a note based on other requests.

    Call them based on the user's request.
    """,
    add_history_to_context=True,
    show_members_responses=True,
    share_member_interactions=True,
    store_events=True,
    store_member_responses=True,
    enable_session_summaries=True,
    num_history_runs=10,
    add_session_summary_to_context=True,
    tool_call_limit=5,
    debug_mode=True,
    debug_level=2,
)

async def main():
    await personal_assistant_team.aprint_response(
        "What is the weather in Tokyo? Can you add an event to the calendar for tomorrow to leave to Tokio? Also, I would like to know about fourier in my notes and in my pdf for this trip to Tokyo.",
        session_id=TEAM_SESSION_ID,
        show_reasoning=True,
        show_full_reasoning=True,
    )

    await personal_assistant_team.aprint_response(
        "Can you remind me what country we talked about visiting? And what did we do before?",
        session_id=TEAM_SESSION_ID,
        show_reasoning=True,
        show_full_reasoning=True,
    )

if __name__ == "__main__":
    asyncio.run(main())