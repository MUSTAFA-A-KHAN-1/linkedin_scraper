import asyncio
import json
import os
from pathlib import Path

from flask import Flask, render_template, request
from linkedin_scraper import BrowserManager, CompanyPostsScraper, CompanyScraper, JobScraper, JobSearchScraper, PersonScraper
from linkedin_scraper.core.exceptions import LinkedInScraperException

app = Flask(__name__)
DEFAULT_SESSION_FILE = "linkedin_session.json"

SCRAPE_TYPES = [
    ("profile", "Person Profile", "Enter a LinkedIn profile URL"),
    ("company", "Company Page", "Enter a LinkedIn company URL"),
    ("company_posts", "Company Posts", "Enter a LinkedIn company URL"),
    ("job", "Job Posting", "Enter a LinkedIn job posting URL"),
    ("job_search", "Job Search", "Enter search keywords"),
]


def as_json(data):
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except TypeError:
        return json.dumps(str(data), indent=2, ensure_ascii=False)


async def run_scrape(session_path, scrape_type, target, location=None, limit=10):
    if not Path(session_path).exists():
        raise FileNotFoundError(f"Session file not found: {session_path}")

    async with BrowserManager(headless=True) as browser:
        await browser.load_session(session_path)

        if scrape_type == "profile":
            scraper = PersonScraper(browser.page)
            result = await scraper.scrape(target)
            return result.model_dump()

        if scrape_type == "company":
            scraper = CompanyScraper(browser.page)
            result = await scraper.scrape(target)
            return result.model_dump()

        if scrape_type == "company_posts":
            scraper = CompanyPostsScraper(browser.page)
            result = await scraper.scrape(target, limit=limit)
            return [item.model_dump() for item in result]

        if scrape_type == "job":
            scraper = JobScraper(browser.page)
            result = await scraper.scrape(target)
            return result.model_dump()

        if scrape_type == "job_search":
            scraper = JobSearchScraper(browser.page)
            result = await scraper.search(keywords=target, location=location, limit=limit)
            return result

        raise ValueError("Unsupported scrape type")


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    form = {
        "scrape_type": "profile",
        "target": "",
        "location": "",
        "limit": 10,
        "session_file": DEFAULT_SESSION_FILE,
    }

    if request.method == "POST":
        form["scrape_type"] = request.form.get("scrape_type", "profile")
        form["target"] = request.form.get("target", "").strip()
        form["location"] = request.form.get("location", "").strip()
        form["limit"] = int(request.form.get("limit", 10) or 10)
        form["session_file"] = request.form.get("session_file", DEFAULT_SESSION_FILE).strip() or DEFAULT_SESSION_FILE

        if form["scrape_type"] != "job_search" and not form["target"]:
            error = "Please enter a valid URL for the selected scrape type."
        elif form["scrape_type"] == "job_search" and not form["target"]:
            error = "Please enter job search keywords."
        else:
            try:
                result_data = asyncio.run(
                    run_scrape(
                        form["session_file"],
                        form["scrape_type"],
                        form["target"],
                        location=form["location"],
                        limit=form["limit"],
                    )
                )
                result = as_json(result_data)
            except FileNotFoundError as exc:
                error = str(exc)
            except LinkedInScraperException as exc:
                error = f"Scraper error: {exc}"
            except Exception as exc:
                error = f"Unexpected error: {exc}"

    return render_template(
        "index.html",
        scrape_types=SCRAPE_TYPES,
        form=form,
        result=result,
        error=error,
        default_session=DEFAULT_SESSION_FILE,
    )


@app.route("/healthz")
def healthz():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
