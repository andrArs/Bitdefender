"""Single MCP server example for the tools chapter."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP  # pyright: ignore[reportMissingImports]

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from section_2.simple_tools import (
    add_calendar_event as add_calendar_event_local,
    get_weather as get_weather_local,
    grep_pdf_chapter as grep_pdf_chapter_local,
    read_schedule as read_schedule_local,
    search_notes as search_notes_local,
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
DEFAULT_SCHEDULE_PATH = str(Path(__file__).resolve().parent / "resources" / "schedule.csv")
DEFAULT_NOTES_DIRECTORY = str(Path(__file__).resolve().parent / "resources" / "notes")

@personal_assistent_mcp.tool()
async def read_schedule(
    schedule_path: str = DEFAULT_SCHEDULE_PATH,
    day: str | None = None,
) -> dict:
    logger.info("read_schedule(%s, day=%s)", schedule_path, day)
    return read_schedule_local(schedule_path, day)


@personal_assistent_mcp.tool()
async def search_notes(
    keyword: str,
    notes_directory: str = DEFAULT_NOTES_DIRECTORY,
    max_results: int = 20,
    context_lines: int = 1,
) -> dict:
    logger.info("search_notes(%s, keyword=%s)", notes_directory, keyword)
    return search_notes_local(notes_directory, keyword, max_results, context_lines)


@personal_assistent_mcp.tool()
async def grep_pdf_chapter(pdf_path: str, heading: str, max_pages: int = 50) -> dict:
    logger.info("grep_pdf_chapter(%s, heading=%s)", pdf_path, heading)
    return grep_pdf_chapter_local(pdf_path, heading, max_pages)


@personal_assistent_mcp.tool()
async def get_weather(location: str) -> dict:
    logger.info("get_weather(%s)", location)
    return get_weather_local(location)


@personal_assistent_mcp.tool()
async def web_search(query: str, max_results: int = 5) -> dict:
    logger.info("web_search(%s)", query)
    return web_search_local(query, max_results)


@personal_assistent_mcp.tool()
async def add_calendar_event(
    calendar_path: str,
    title: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    location: str = "",
) -> dict:
    logger.info("add_calendar_event(%s, title=%s)", calendar_path, title)
    return add_calendar_event_local(
        calendar_path,
        title,
        start_iso,
        end_iso,
        description,
        location,
    )


if __name__ == "__main__":
    personal_assistent_mcp.run(transport="streamable-http")
