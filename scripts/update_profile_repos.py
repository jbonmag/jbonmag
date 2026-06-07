"""Update the public repository table in the profile README."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


OWNER = "jbonmag"
README = Path("README.md")
START = "<!-- REPOS:START -->"
END = "<!-- REPOS:END -->"
LATEST_START = "<!-- LATEST:START -->"
LATEST_END = "<!-- LATEST:END -->"
EXCLUDED_REPOS = set()
DESCRIPTION_OVERRIDES = {
    "42": "42Barcelona systems, C and algorithms projects.",
    "Amazon-Product-Reviews-Classifier-with-PySpark": "Sentiment classifier for Amazon product reviews using PySpark MLlib.",
    "Esquema-ML-PySpark-Databricks": "Reference PySpark ML pipeline for Databricks.",
    "Housing-ML": "Housing price prediction project for the Ames dataset.",
    "LM_Conversacional_Basico": "Basic conversational language model fine-tuning project.",
    "Titanic-ML": "Titanic survival prediction project.",
    "local-rag-pgvector": "Local RAG project using PostgreSQL and pgvector.",
}


def fetch_public_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    token = os.environ.get("GITHUB_TOKEN", "")

    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?type=owner&sort=pushed&direction=desc&per_page=100&page={page}"
        )
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"{OWNER}-profile-updater",
                **({"Authorization": f"Bearer {token}"} if token else {}),
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                batch = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise SystemExit(f"Could not fetch repositories: {exc}") from exc

        if not batch:
            break

        repos.extend(batch)
        page += 1

    return repos


def clean_description(repo: dict) -> str:
    if repo.get("name") in DESCRIPTION_OVERRIDES:
        return DESCRIPTION_OVERRIDES[repo["name"]]

    description = repo.get("description") or ""
    description = " ".join(description.split())
    if description:
        return description
    return "Public repository."


def repo_table(repos: list[dict]) -> str:
    visible = [
        repo
        for repo in repos
        if not repo.get("archived")
        and repo.get("name") not in EXCLUDED_REPOS
        and repo.get("name") != OWNER
    ]

    lines = [
        "| Repository | Description | Main language |",
        "| --- | --- | --- |",
    ]

    for repo in visible:
        name = repo["name"]
        url = repo["html_url"]
        description = clean_description(repo).replace("|", "\\|")
        language = repo.get("language") or "Not specified"
        lines.append(f"| [{name}]({url}) | {description} | {language} |")

    return "\n".join(lines)


def latest_work(repos: list[dict], limit: int = 5) -> str:
    visible = [
        repo
        for repo in repos
        if not repo.get("archived")
        and repo.get("name") not in EXCLUDED_REPOS
        and repo.get("name") != OWNER
    ]

    visible.sort(key=lambda repo: repo.get("pushed_at") or "", reverse=True)

    lines = []
    for repo in visible[:limit]:
        name = repo["name"]
        url = repo["html_url"]
        description = clean_description(repo).replace("\n", " ")
        lines.append(f"- [{name}]({url}) - {description}")

    return "\n".join(lines)


def replace_block(content: str, start: str, end: str, replacement: str) -> str:
    if start not in content or end not in content:
        raise SystemExit(f"Markers were not found: {start} / {end}")

    before, rest = content.split(start, 1)
    _, after = rest.split(end, 1)
    return f"{before}{start}\n{replacement}\n{end}{after}"


def update_readme(table: str, latest: str) -> bool:
    content = README.read_text(encoding="utf-8")
    updated = replace_block(content, START, END, table)
    updated = replace_block(updated, LATEST_START, LATEST_END, latest)

    if updated == content:
        return False

    README.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    repos = fetch_public_repos()
    table = repo_table(repos)
    latest = latest_work(repos)
    changed = update_readme(table, latest)
    print("README.md updated" if changed else "README.md already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
