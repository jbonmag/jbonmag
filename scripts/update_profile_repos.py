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
EXCLUDED_REPOS = set()
DESCRIPTION_OVERRIDES = {
    "42": "42Barcelona projects and exercises.",
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


def update_readme(table: str) -> bool:
    content = README.read_text(encoding="utf-8")
    if START not in content or END not in content:
        raise SystemExit("Repository markers were not found in README.md")

    before, rest = content.split(START, 1)
    _, after = rest.split(END, 1)
    updated = f"{before}{START}\n{table}\n{END}{after}"

    if updated == content:
        return False

    README.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    table = repo_table(fetch_public_repos())
    changed = update_readme(table)
    print("README.md updated" if changed else "README.md already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
