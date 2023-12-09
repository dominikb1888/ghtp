from collections import OrderedDict
from collections import Counter
from datetime import datetime, timedelta
import json
import os
from urllib.request import urlopen, Request

import typer
from rich import print
from rich.progress import track
from rich.table import Table
from sparklines import sparklines

cli = typer.Typer()

# TODO: Check if .env file exists if not ask user to create one
# TODO: authenticate via gh?
if os.environ.get("GHTOKEN"):
    config = {
        "GHTOKEN": os.environ.get("GHTOKEN"),
        "GUSER": os.environ.get("GHUSER"),
    }
else:
    env = "../.env" if os.path.exists("../.env") else ".env"
    with open(env) as f:
        config = {}
        for line in f.readlines():
            k, v = line.strip().split("=")
            config[k] = v

headers = {
    "Authorization": f"token {config['GHTOKEN']}",
    "Accept": "application/vnd.github.v3+json",
}


def complete_group():
    url = "https://api.github.com/user/orgs"
    httprequest = Request(url, headers=headers)
    with urlopen(httprequest) as response:
        if response.status == 200:
            data = json.loads(response.read().decode())
    groups = [group["login"] for group in data]

    return groups if groups else ["23W-GBAC"]


def get_repos(group: str) -> list:
    """TODO"""
    url = f"https://api.github.com/orgs/{group}/repos?per_page=100"
    httprequest = Request(url, headers=headers)
    with urlopen(httprequest) as response:
        if response.status == 200:
            data = json.loads(response.read().decode())
            names = []
            for repo in data:
                names.append(repo["name"])
        else:
            print(f"Failed to fetch repos. Status code: {response.status_code}")
    return names if names else []


def get_commit_histogram(commits):
    """TODO"""
    dates = [
        str(
            datetime.strptime(
                commit["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ"
            ).date()
        )
        for commit in commits
    ]
    count = dict(Counter(dates))
    return count


def get_commits(group: str, names: list) -> dict:
    """TODO"""
    updates = OrderedDict()
    total = 0
    for name in track(names, description="Loading Updates..."):
        total += 1
        url = f"https://api.github.com/repos/{group}/{name}/commits?per_page=1000"
        httprequest = Request(url, headers=headers)
        with urlopen(httprequest) as response:
            if response.status == 200:
                data = sorted(
                    json.loads(response.read().decode()),
                    key=lambda x: datetime.strptime(
                        x["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ"
                    ),
                )
                dates = get_commit_histogram(data)
                latest = data[-1]
                date = datetime.strptime(
                    latest["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ"
                )
                message = latest["commit"]["message"].replace("\n", " ")
                author = latest["author"]
                if author:
                    updates[author["login"]] = {
                        "date": date,
                        "url": latest["html_url"],
                        "message": message,
                        "author": author,
                        "dates": dates,
                        "start": datetime.strptime(list(dates.keys())[0], "%Y-%m-%d"),
                        "end": datetime.strptime(list(dates.keys())[-1], "%Y-%m-%d"),
                    }
            else:
                print(f"Failed to fetch commits. Status code: {response.status_code}")

    print(f"Loaded {total} Repos.")

    first = min(update["start"] for _, update in updates.items())
    last = max(update["end"] for _, update in updates.items())
    td = last - first
    date_dct = dict.fromkeys(
        [
            datetime.strftime(first + timedelta(days=x), "%Y-%m-%d")
            for x in range(int(td.days))
        ],
        0,
    )

    for _, update in updates.items():
        update["dates"] = sparklines(list({**date_dct, **update["dates"]}.values()))

    return updates


def commit_table(commits: dict) -> Table:
    """TODO"""
    table = Table(title="Latest Blog Updates")
    table.add_column("Date", justify="right", style="cyan", no_wrap=True)
    table.add_column("Sparklines")
    table.add_column("Name", style="magenta")
    table.add_column("URL", style="green")

    for author, data in reversed(sorted(commits.items(), key=lambda x: x[1]["date"])):
        name = f"[link={data['url']}]{author}[/link]"
        message = data["message"]
        sparklines = "".join(data["dates"])
        date_str = datetime.strftime(data["date"], "%d-%m-%Y")
        table.add_row(date_str, sparklines, name, message)

    return table


@cli.command()
def gallery(
    group: str = typer.Argument(
        help="The Github Group to collect.",
        autocompletion=complete_group,
    ),
):
    "Creates a markdown image gallery from all users commiting to a group"

    names = get_repos(group)
    commits = get_commits(group, names)
    print(commit_table(commits))
