"""Multiple MCP servers mounted into one FastAPI app."""

from __future__ import annotations

import contextlib
import logging
import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP  # pyright: ignore[reportMissingImports]

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from section_2.simple_tools import (
    add_calendar_event as add_calendar_event_local,
    get_weather as get_weather_local,
    grep_pdf_chapter as grep_pdf_chapter_local,
    read_schedule as read_schedule_local,
    search_notes as search_notes_local,
    save_study_note as save_study_note_local,
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


logger = setup_logger("my_logger")

personal_assistent_mcp = FastMCP("Personal Assistant Server", stateless_http=True)
college_buddy_assistent_mcp = FastMCP("College Buddy Server", stateless_http=True)
DEFAULT_SCHEDULE_PATH = str(Path(__file__).resolve().parent / "resources" / "schedule.csv")
DEFAULT_NOTES_DIRECTORY = str(Path(__file__).resolve().parent / "resources" / "notes")
DEFAULT_PDF_PATH = str(Path(__file__).resolve().parent / "resources" / "class_notes.pdf")
DEFAULT_CALENDAR_PATH = str(Path(__file__).resolve().parent / "resources" / "calendar.ics")


@personal_assistent_mcp.tool()
async def read_schedule(
    day: str | None = None,
) -> dict:
    """Read the class schedule CSV and group entries by day.

    Use this when the agent needs to inspect the timetable or answer
    day-based questions like "what happens on Monday?". The schedule file is
    loaded from `.env`, so the agent does not need to invent a path. The
    optional `day` filter should be a weekday name such as `Monday` or
    `Tuesday`.

    Returns the raw schedule rows grouped by day so the model can reason over
    the original source data instead of a rewritten summary.
    """
    schedule_path = os.getenv("SCHEDULE_PATH", DEFAULT_SCHEDULE_PATH)
    logger.info("personal.read_schedule(%s, day=%s)", schedule_path, day)
    return read_schedule_local(schedule_path, day)


@personal_assistent_mcp.tool()
async def get_weather(location: str) -> dict:
    """Fetch weather for a city, country, or location name.

    Use this for short real-world location queries like `Bucharest`,
    `Romania`, or `London, UK`. Do not pass arbitrary topics or long questions;
    the tool forwards the value directly to the weather service.

    Returns a small structured weather snapshot for the requested place.
    """
    logger.info("personal.get_weather(%s)", location)
    return get_weather_local(location)


@personal_assistent_mcp.tool()
async def web_search(query: str, max_results: int = 5) -> dict:
    """Search the web for a short query and return a small result list.

    Use this when the agent needs fresh information from the internet. Pass a
    query string such as `cute cats`, `lagrange interpolation`, or
    `OpenRouter free models`. The `max_results` value controls how many links
    are returned, not how many sources are searched internally.

    The result contains the query, the number of returned items, the search
    source, and a list of result titles/URLs.
    """
    logger.info("personal.web_search(%s)", query)
    return web_search_local(query, max_results)


@personal_assistent_mcp.tool()
async def add_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    location: str = "",
) -> dict:
    """Append a new event to a local calendar file.

    Use this as the write-tool example when the agent needs to change stored
    calendar data. The calendar file is loaded from `.env`, so the agent only
    supplies the event details. `start_iso` and `end_iso` should be ISO 8601
    strings, such as `2026-06-05T10:00:00`.

    This is a state-changing tool, so it is the best place to discuss trust,
    permissions, and side effects.
    """
    calendar_path = os.getenv("CALENDAR_PATH", DEFAULT_CALENDAR_PATH)
    logger.info("personal.add_calendar_event(%s, title=%s)", calendar_path, title)
    return add_calendar_event_local(
        calendar_path,
        title,
        start_iso,
        end_iso,
        description,
        location,
    )






@college_buddy_assistent_mcp.tool()
async def search_notes(
    keyword: str,
    max_results: int = 20,
    context_lines: int = 1,
) -> dict:
    """Search a Markdown notes folder for a keyword.

    Use this for local knowledge retrieval over lecture notes or study
    material. The notes folder is loaded from `.env`, so the agent does not
    need to provide a path. `context_lines` controls how much text appears
    around each hit, while `max_results` limits how many files are returned.

    The output groups matches by file so the agent can compare sources easily.
    """
    notes_directory = os.getenv("NOTES_DIRECTORY", DEFAULT_NOTES_DIRECTORY)
    logger.info("college.search_notes(%s, keyword=%s)", notes_directory, keyword)
    return search_notes_local(notes_directory, keyword, max_results, context_lines)


@college_buddy_assistent_mcp.tool()
async def grep_pdf_chapter(
    heading: str,
    max_pages: int = 50,
) -> dict:
    """Find a heading in a PDF and return matching paragraphs.

    Use this when the agent needs document retrieval from a PDF, not a full
    summary. The PDF file is loaded from `.env`, so the agent only provides
    the heading or keyword to search for. The tool only scans the first
    `max_pages` pages, which keeps the demo fast and makes the scope explicit.

    The result returns a list of matches with page numbers and paragraph text.
    """
    pdf_path = os.getenv("PDF_PATH", DEFAULT_PDF_PATH)
    logger.info("college.grep_pdf_chapter(%s, heading=%s)", pdf_path, heading)
    return grep_pdf_chapter_local(pdf_path, heading, max_pages)


@college_buddy_assistent_mcp.tool()
async def save_study_note(
    title: str,
    body: str,
    filename: str | None = None,
) -> dict:
    """Write a Markdown study note into the notes folder.

    Use this as the write-tool example for the College Buddy agent. The notes
    folder is loaded from `.env`, so the agent only provides a short title and
    the note body. If `filename` is omitted, the tool generates a safe
    Markdown filename automatically.

    This is useful for teaching the difference between read tools and write
    tools because it changes local state.
    """
    notes_directory = os.getenv("NOTES_DIRECTORY", DEFAULT_NOTES_DIRECTORY)
    logger.info("college.save_study_note(%s, title=%s)", notes_directory, title)
    return save_study_note_local(notes_directory, title, body, filename)


personal_app = personal_assistent_mcp.streamable_http_app()
college_app = college_buddy_assistent_mcp.streamable_http_app()

def combined_lifespan(proxy_apps):
    @contextlib.asynccontextmanager
    async def lifespan(app):
        async with contextlib.AsyncExitStack() as stack:
            for proxy_app in proxy_apps:
                await stack.enter_async_context(proxy_app.router.lifespan_context(app))
            yield

    return lifespan


app = FastAPI(debug=True, lifespan=combined_lifespan([personal_app, college_app]))
app.mount("/mcp/personal", personal_app)
app.mount("/mcp/college", college_app)


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8200)


if __name__ == "__main__":
    main()
