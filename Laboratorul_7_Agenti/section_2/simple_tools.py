"""Reusable tools for the MCP chapter.

These functions are intentionally plain Python so students can call them
directly first, then expose the same behavior through MCP servers later.
"""

from __future__ import annotations

import csv
import html
import base64
from html.parser import HTMLParser
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from pypdf import PdfReader  # pyright: ignore[reportMissingImports]

DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_USER_AGENT = "Lab_Agents/section_2"


def _request(method: str, url: str, **kwargs: Any) -> requests.Response:
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    headers.update(kwargs.pop("headers", {}))
    response = requests.request(
        method,
        url,
        headers=headers,
        timeout=kwargs.pop("timeout", DEFAULT_TIMEOUT_SECONDS),
        **kwargs,
    )
    response.raise_for_status()
    return response


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _first_value(row: dict[str, str], *names: str, default: str = "") -> str:
    lower_map = {
        key.lower(): value.strip()
        for key, value in row.items()
        if key and value is not None
    }
    for name in names:
        value = lower_map.get(name.lower())
        if value:
            return value
    return default


def _parse_csv_schedule(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows: list[dict[str, Any]] = []
        for row in reader:
            if not any(value and value.strip() for value in row.values() if value is not None):
                continue
            rows.append(row)
    return rows


def _weekday_from_row(row: dict[str, Any]) -> str:
    return _first_value(row, "day", "weekday", "date", default="unknown").strip()


def _row_matches_day(row: dict[str, Any], day: str | None) -> bool:
    if not day:
        return True

    normalized_day = day.strip().lower()
    row_day = _weekday_from_row(row).lower()
    return row_day == normalized_day


def read_schedule(
    schedule_path: str | Path,
    day: str | None = None,
) -> dict[str, Any]:
    """Read a local CSV schedule file grouped by day.

    The tool returns the raw CSV rows so students can see the source data
    directly. If `day` is provided, only that day's rows are returned.
    """

    path = Path(schedule_path)
    if path.suffix.lower() != ".csv":
        raise ValueError("Schedule files must end in .csv")

    rows = _parse_csv_schedule(path)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        row_day = _weekday_from_row(row)
        if not _row_matches_day(row, day):
            continue
        grouped.setdefault(row_day, []).append(row)

    if day:
        matched_rows = grouped.get(day.strip(), grouped.get(day.title(), []))
        if not matched_rows:
            matched_rows = grouped.get(day.strip().title(), [])
        return {
            "source": str(path),
            "day_filter": day,
            "count": len(matched_rows),
            "entries": matched_rows,
        }

    days = [
        {
            "day": row_day,
            "count": len(day_rows),
            "entries": day_rows,
        }
        for row_day, day_rows in grouped.items()
    ]
    return {
        "source": str(path),
        "day_filter": None,
        "count": sum(len(day_rows) for day_rows in grouped.values()),
        "days": days,
    }


def search_notes(
    notes_directory: str | Path,
    keyword: str,
    max_results: int = 20,
    context_lines: int = 1,
) -> dict[str, Any]:
    """Search Markdown notes for a keyword.

    `context_lines` controls how many surrounding lines are included around
    each hit. `max_results` limits how many files are returned, not how many
    total matches are scanned.
    """

    base = Path(notes_directory)
    keyword_lower = keyword.lower()
    file_matches: list[dict[str, Any]] = []

    for path in sorted(base.rglob("*.md")):
        lines = _read_text(path).splitlines()
        hits: list[dict[str, Any]] = []
        for index, line in enumerate(lines, start=1):
            if keyword_lower not in line.lower():
                continue
            start = max(1, index - context_lines)
            end = min(len(lines), index + context_lines)
            hits.append(
                {
                    "line": index,
                    "snippet": "\n".join(lines[start - 1 : end]),
                }
            )
        if hits:
            file_matches.append(
                {
                    "file": str(path),
                    "match_count": len(hits),
                    "matches": hits,
                }
            )

    return {
        "query": keyword,
        "directory": str(base),
        "file_count": len(file_matches),
        "count": sum(file_match["match_count"] for file_match in file_matches),
        "files": file_matches[:max_results],
    }


def save_study_note(
    notes_directory: str | Path,
    title: str,
    body: str,
    filename: str | None = None,
) -> dict[str, Any]:
    """Write a markdown study note into the notes directory."""

    directory = Path(notes_directory)
    directory.mkdir(parents=True, exist_ok=True)

    if filename:
        note_name = filename if filename.lower().endswith(".md") else f"{filename}.md"
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "study-note"
        note_name = f"{slug}-{uuid.uuid4().hex[:8]}.md"

    path = directory / note_name
    content = "\n".join([f"# {title}", "", body.strip(), ""])
    path.write_text(content, encoding="utf-8")
    return {
        "message": "Study note saved",
        "path": str(path),
        "title": title,
    }


def _is_heading_like(line: str) -> bool:
    candidate = line.strip()
    if not candidate:
        return False
    if candidate.startswith("#"):
        return True
    if re.match(r"^(chapter|section|appendix)\b", candidate, re.I):
        return True
    if len(candidate) <= 120 and candidate.upper() == candidate and any(
        ch.isalpha() for ch in candidate
    ):
        return True
    return False


def grep_pdf_chapter(
    pdf_path: str | Path,
    heading: str,
    max_pages: int = 50,
) -> dict[str, Any]:
    """Extract paragraphs containing a heading from the first pages of a PDF."""

    path = Path(pdf_path)
    reader = PdfReader(str(path))
    heading_lower = heading.lower()
    matches: list[dict[str, Any]] = []

    def split_paragraphs(text: str) -> list[str]:
        paragraphs: list[str] = []
        current: list[str] = []
        for line in text.splitlines():
            if line.strip():
                current.append(line.strip())
                continue
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
        if current:
            paragraphs.append(" ".join(current).strip())
        return [paragraph for paragraph in paragraphs if paragraph]

    for page_number, page in enumerate(reader.pages[:max_pages], start=1):
        text = page.extract_text() or ""
        for paragraph_index, paragraph in enumerate(split_paragraphs(text), start=1):
            if heading_lower not in paragraph.lower():
                continue
            matches.append(
                {
                    "page": page_number,
                    "paragraph_index": paragraph_index,
                    "paragraph": paragraph,
                }
            )

    if not matches:
        return {
            "source": str(path),
            "heading": heading,
            "found": False,
            "count": 0,
            "matches": [],
        }

    return {
        "source": str(path),
        "heading": heading,
        "found": True,
        "count": len(matches),
        "matches": matches,
    }


def get_weather(location: str) -> dict[str, Any]:
    """Fetch a weather summary from wttr.in without an API key."""

    response = _request(
        "GET",
        f"https://wttr.in/{quote_plus(location)}",
        params={"format": "j1"},
    )
    payload = response.json()
    current = payload.get("current_condition", [{}])[0]
    astronomy = payload.get("weather", [{}])[0].get("astronomy", [{}])[0]
    return {
        "location": location,
        "temperature_c": current.get("temp_C"),
        "feels_like_c": current.get("FeelsLikeC"),
        "humidity": current.get("humidity"),
        "wind_kph": current.get("windspeedKmph"),
        "condition": current.get("weatherDesc", [{}])[0].get("value", ""),
        "observation_time": current.get("observation_time"),
        "sunrise": astronomy.get("sunrise"),
        "sunset": astronomy.get("sunset"),
    }


def _clean_duckduckgo_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("duckduckgo.com"):
        query = parse_qs(parsed.query)
        candidate = query.get("uddg")
        if candidate:
            return unquote(candidate[0])
    return url


def _clean_bing_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.endswith("bing.com") and parsed.path == "/ck/a":
        query = parse_qs(parsed.query)
        candidate = query.get("u")
        if candidate:
            token = candidate[0]
            if token.startswith("a1"):
                token = token[2:]
            padding = "=" * (-len(token) % 4)
            try:
                return base64.urlsafe_b64decode(token + padding).decode("utf-8")
            except Exception:
                pass
    return html.unescape(url)


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", html.unescape(value)).strip()


class _BingParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._capture = False
        self._current_href = ""
        self._current_title: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a" and self._capture:
            return
        if tag == "a":
            attributes = {key: value or "" for key, value in attrs}
            href = attributes.get("href", "")
            if href.startswith("http"):
                self._capture = True
                self._current_href = href
                self._current_title = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._current_title.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._capture:
            return
        title = _strip_html("".join(self._current_title))
        if title and self._current_href:
            self.results.append(
                {
                    "title": title,
                    "url": html.unescape(self._current_href),
                }
            )
        self._capture = False
        self._current_href = ""
        self._current_title = []


class _DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self.candidate_links = 0
        self._capture = False
        self._current_href = ""
        self._current_title: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = {key: value or "" for key, value in attrs}
        classes = attributes.get("class", "").split()
        if "result__a" in classes:
            self.candidate_links += 1
            self._capture = True
            self._current_href = attributes.get("href", "")
            self._current_title = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._current_title.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self._capture:
            return
        title = _strip_html("".join(self._current_title))
        if title and self._current_href:
            self.results.append(
                {
                    "title": title,
                    "url": _clean_duckduckgo_url(self._current_href),
                }
            )
        self._capture = False
        self._current_href = ""
        self._current_title = []


def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Search the web using HTML result pages.

    Bing is used first because it tends to be more stable for classroom demos.
    DuckDuckGo remains a fallback when Bing does not return usable results.
    """

    response = _request(
        "GET",
        "https://www.bing.com/search",
        params={"q": query},
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )
    raw_pairs = re.findall(r'<h2[^>]*><a[^>]+href="([^"]+)"[^>]*>(.*?)</a></h2>', response.text, re.S)
    bing_results: list[dict[str, str]] = []
    for href, title in raw_pairs:
        clean_title = _strip_html(title)
        if not clean_title:
            continue
        bing_results.append(
            {
                "title": clean_title,
                "url": _clean_bing_url(html.unescape(href)),
            }
        )

    results = bing_results[:max_results]
    if results:
        return {
            "query": query,
            "count": len(results),
            "source": "bing",
            "results": results,
        }

    response = _request(
        "GET",
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )
    parser = _DuckDuckGoParser()
    parser.feed(response.text)
    results = parser.results[:max_results]
    if results:
        return {
            "query": query,
            "count": len(results),
            "source": "duckduckgo_html",
            "results": results,
        }

    return {
        "query": query,
        "count": 0,
        "source": "none",
        "results": [],
    }


def _format_ics_datetime(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.strftime("%Y%m%dT%H%M%S")


def _escape_ics_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\r\n", "\\n").replace("\n", "\\n")


def add_calendar_event(
    calendar_path: str | Path,
    title: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    location: str = "",
) -> dict[str, Any]:
    """Append an event to a local .ics calendar file."""

    path = Path(calendar_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    event_uid = f"{uuid.uuid4().hex}@lab-ai-agents"
    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{event_uid}",
        f"DTSTAMP:{_format_ics_datetime(datetime.utcnow().isoformat())}",
        f"SUMMARY:{_escape_ics_text(title)}",
        f"DTSTART:{_format_ics_datetime(start_iso)}",
        f"DTEND:{_format_ics_datetime(end_iso)}",
    ]
    if description:
        event_lines.append(f"DESCRIPTION:{_escape_ics_text(description)}")
    if location:
        event_lines.append(f"LOCATION:{_escape_ics_text(location)}")
    event_lines.append("END:VEVENT")
    event_block = "\n".join(event_lines)

    if path.exists():
        content = _read_text(path).strip()
        if content.endswith("END:VCALENDAR"):
            content = content[:-len("END:VCALENDAR")].rstrip()
            new_content = f"{content}\n\n{event_block}\nEND:VCALENDAR\n"
        else:
            new_content = f"{content}\n\n{event_block}\n"
    else:
        new_content = "\n".join(
            [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Lab Agents//EN",
                event_block,
                "END:VCALENDAR",
                "",
            ]
        )

    path.write_text(new_content, encoding="utf-8")
    return {
        "message": "Calendar event saved",
        "path": str(path),
        "event": {
            "title": title,
            "start": start_iso,
            "end": end_iso,
            "description": description,
            "location": location,
            "uid": event_uid,
        },
    }
