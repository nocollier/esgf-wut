import importlib
import json
from typing import Literal, Optional

import typer
import yaml

import esgf_wut as wut

app = typer.Typer(
    name="wut",
    no_args_is_help=True,
    add_completion=False,
)


@app.command(
    help="Build an ESGF faceted search by specifying terms in the control vocabular universe.",
)
def query(
    terms: list[str],
    project: Optional[str] = None,
    regen_database: bool = False,
    format: Literal["pandas", "json", "yaml"] = "pandas",
):
    database_file = importlib.resources.files("esgf_wut.data") / "esgf_cv_universe.db"
    if regen_database and database_file.is_file():
        database_file.unlink()
    out = wut.query_cv_universe(terms, project)
    if format == "pandas":
        print(out.to_string())
    else:
        out = wut.query_df_to_dict(out)
        if format == "json":
            print(json.dumps(out))
        elif format == "yaml":
            print(yaml.dump(out))
        else:
            raise ValueError("Unknown output format.")


if __name__ == "__main__":
    app()
