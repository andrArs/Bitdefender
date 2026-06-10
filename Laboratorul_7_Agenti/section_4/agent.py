import asyncio
import sys
from pathlib import Path

from agno.agent import Agent

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from section_3.models import model_gemma_4_31b_it, model_gemma_4_26b_a4b_it, model_hermes_3_llama_3_1_405b, model_nvidia_nano_omni_30b_a3b_reasoning, model_nvidia_super_120b_a12b

# from section_3.models import FAST_MODEL, BALANCED_MODEL, STRONG_MODEL, NVIDIA_MODEL, NIVIDIA_MODEL_2
from section_4.tools import PERSONAL_ASSISTANT_TOOLS, COLLEGE_BUDDY_TOOLS

import asyncio

agent = Agent(
    model=model_nvidia_super_120b_a12b,
    markdown=True,
    tools=[PERSONAL_ASSISTANT_TOOLS, COLLEGE_BUDDY_TOOLS],
    role="You are a helpful assistant that can help with personal and college related tasks.",
    description="You are a helpful assistant that can help with personal and college related tasks.",
    expected_output="The response should be in markdown format and pretty printed for the user to read. You can use dashes, tables, strings, everything that you consider to use.",
    instructions="""
    You have access to two MCP tool groups:
    - `PERSONAL_ASSISTANT_TOOLS`
    - `COLLEGE_BUDDY_TOOLS`

    Use the tools exactly as follows:
    - Use `read_schedule` when the user asks about the timetable, a weekday,
      class hours, or what happens on a specific day.
    - Use `get_weather` when the user asks about the weather in a city,
      country, or place name.
    - Use `web_search` when the user needs fresh information from the web, a
      recent fact, or a general internet search.
    - Use `add_calendar_event` when the user wants to add or change an event in
      the calendar. This is a write action, so use it only when the user wants
      to modify the calendar.

    - Use `search_notes` when the user asks to find something inside the
      Markdown notes folder, especially by keyword or topic.
    - Use `grep_pdf_chapter` when the user asks for a chapter, heading, or
      specific section inside the PDF document.
    - Use `save_study_note` when the user wants to create or save a new study
      note in Markdown format.

    If the user asks something related to schedules, notes, documents, weather,
    search, or saving information, prefer the matching tool instead of
    answering from memory.
    If a tool can answer directly, call it first and then explain the result
    clearly in markdown.
    """,
    debug_mode=True,
    debug_level=2
)

personal_assistant_agent = Agent(
    model=model_nvidia_super_120b_a12b,
    name="Personal Assistant Agent",
    id="personal_assistant_agent",
    role="You are a helpful assistant that can help with personal related tasks.",
    description="You are a helpful assistant that can help with personal related tasks.",
    expected_output="The response should be in markdown format and pretty printed for the user to read. You can use dashes, tables, strings, everything that you consider to use.",
    instructions="""
    You have access to the following tools:
    - `read_schedule` to which you will pass the day you want to know the schedule for.
    - `get_weather` to which you will pass the city/country/region you want to know the weather for.
    - `web_search` to which you will pass the query you want to search for.
    - `add_calendar_event` to which you will pass the event you want to add to the calendar.

    If the user asks something related to schedules, notes, documents, weather,
    search, or saving information, prefer the matching tool instead of
    answering from memory.
    If a tool can answer directly, call it first and then explain the result
    clearly in markdown.
    """,
    tools=[PERSONAL_ASSISTANT_TOOLS],

    add_history_to_context=True,
    num_history_runs=10,
    add_session_summary_to_context=True,
    tool_call_limit=3,
    debug_mode=True,
    debug_level=2
)

college_buddy_agent = Agent(
    model=model_nvidia_super_120b_a12b,
    name="College Buddy Agent",
    id="college_buddy_agent",
    role="You are a helpful assistant that can help with college related tasks.",
    description="You are a helpful assistant that can help with college related tasks.",
    expected_output="The response should be in markdown format and pretty printed for the user to read. You can use dashes, tables, strings, everything that you consider to use.",
    instructions="""
    You have access to the following tools:
    - `search_notes` to which you will pass the query you want to search for.
    - `grep_pdf_chapter` to which you will pass the chapter you want to search for.
    - `grep_pdf_section` to which you will pass the section you want to search for.
    - `save_study_note` to which you will pass the note you want to save.

    If the user asks something related to notes, documents, search, or saving information, prefer the matching tool instead of
    answering from memory.
    If a tool can answer directly, call it first and then explain the result
    clearly in markdown.
    """,
    tools=[COLLEGE_BUDDY_TOOLS],

    add_history_to_context=True,
    num_history_runs=10,
    add_session_summary_to_context=True,
    tool_call_limit=3,
    debug_mode=True,
    debug_level=2
)


async def main() -> None:
    await agent.aprint_response("What is my schedule for Monday?")

if __name__ == "__main__":
    asyncio.run(main())