from collections import OrderedDict
import json
import os
from urllib.request import urlopen, Request

import click
import typer
from rich import print
from rich.progress import track
from rich.table import Table

cli = typer.Typer()


@click.group()
@click.version_option()
def cli():
    "A set of github tools for managing groups"


@cli.command(name="gallery")
@click.argument("ghorg")
@click.option(
    "-o",
    "--option",
    help="An example option",
)
def gallery(ghorg, option):
    "Creates a markdown image gallery from all users commiting to a group"

    ## TODO: Check if .env file exists if not ask user to create one
    ## TODO: authenticate via gh?
    if os.environ.get("GHTOKEN"):
        config = {
            "GHTOKEN": os.environ.get("GHTOKEN"),
            "GHORG": os.environ.get("GHORG"),
        }
    else:
        env = "../.env" if os.path.exists("../.env") else ".env"
        with open(env) as f:
            config = {}
            for line in f.readlines():
                k, v = line.strip().split("=")
                config[k] = v

            config["GHORG"] = ghorg

    headers = {
        "Authorization": f"token {config['GHTOKEN']}",
        "Accept": "application/vnd.github.v3+json",
    }

    url = f"https://api.github.com/orgs/{config['GHORG']}/repos?per_page=100"
    httprequest = Request(url, headers=headers)
    with urlopen(httprequest) as response:
        if response.status == 200:
            data = json.loads(response.read().decode())
            names = []
            for repo in data:
                names.append(repo["name"])
        else:
            print(f"Failed to fetch repos. Status code: {response.status_code}")

    authors = OrderedDict()
    total = 0
    for name in track(names, description="Loading Commits..."):
        total += 1
        url = f"https://api.github.com/repos/{config['GHORG']}/{name}/commits"
        httprequest = Request(url, headers=headers)
        with urlopen(httprequest) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                date = data["commit"]["author"]["date"]
                author = data[0]["author"]
                if author:
                    authors[date] = author
            else:
                print(f"Failed to fetch commits. Status code: {response.status_code}")

    print(f"Loaded {total} commits.")

    table = Table(title="Latest Blog Updates")

    table.add_column("Date", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("URL", style="green")

    for date, author in authors.items():
        name = author["login"]
        img = author["avatar_url"]
        table.add_row(date, name, img)
