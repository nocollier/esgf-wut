import importlib
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import yaml


def _get_database_file() -> Path:
    database_file = importlib.resources.files("esgf_wut.data") / "esgf_cv_universe.db"
    if not database_file.is_file():
        yaml_file = importlib.resources.files("esgf_wut.data") / "database_facets.yaml"
        with open(yaml_file) as fin:
            facets_by_project = yaml.safe_load(fin)
        ingest_by_facet_query(database_file, facets_by_project)
    return database_file


def query_cv_universe(terms: list[str], project: Optional[str] = None) -> pd.DataFrame:
    database_file = _get_database_file()
    con = sqlite3.connect(str(database_file))
    q = " OR ".join([f"TermName LIKE '{t.replace('*', '%')}'" for t in terms])
    if project is not None:
        q = f"(ProjectName LIKE '{project}') AND ({q})"
    df = pd.read_sql_query(
        f"""
    SELECT TermName, CollectionName, ProjectName
    FROM Terms 
    INNER JOIN Collections 
    ON Terms.CollectionId = Collections.CollectionId
    WHERE {q}
    ORDER BY ProjectName;""",
        con,
    )
    df = df.groupby(["ProjectName", "CollectionName"]).agg(lambda gr: gr)
    return df


def query_df_to_dict(df) -> dict[str, dict[str, list[str]]]:
    out = {
        project: {
            key: list(val) if pd.api.types.is_list_like(val) else val
            for key, val in df.loc[project].to_dict()["TermName"].items()
        }
        for project in df.index.get_level_values(0).unique()
    }
    return out


def create_cv_universe(path: Path, ingest_data: list[tuple[str, str, str]]) -> None:
    """
    Create a SQLite database with CV terms.

    Parameters
    ----------
    path
        The full path to the database file.
    ingest_data
        A list of tuples of the form (term, collection, project) to be ingested.
        For example, [('CESM2','source_id','CMIP6'),('tas','variable','CMIP5')].
    """
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Collections(
    CollectionId   INTEGER PRIMARY KEY, 
    CollectionName TEXT NOT NULL,
    ProjectName    TEXT NOT NULL,
    UNIQUE(CollectionName, ProjectName)
    );""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Terms(
    TermId    INTEGER PRIMARY KEY, 
    TermName  TEXT NOT NULL,
    CollectionId INTEGER NOT NULL,
    FOREIGN KEY(CollectionId) REFERENCES Collections(CollectionId),
    UNIQUE(TermName, CollectionId) 
    );""")
    for term, collection, project in ingest_data:
        # Try to insert a new category, ignore if already present
        cur.execute(
            f"INSERT INTO Collections (CollectionId,CollectionName,ProjectName) VALUES (NULL,'{collection}','{project}') ON CONFLICT DO NOTHING"
        )
        # Get the collection id so we can insert the term
        collection_id = cur.execute(
            f"SELECT CollectionId FROM Collections WHERE CollectionName='{collection}' AND ProjectName='{project}'"
        ).fetchone()
        assert len(collection_id) == 1
        # Now insert the term
        cur.execute(
            f"INSERT INTO Terms (TermId,TermName,CollectionId) VALUES (NULL,'{term}','{collection_id[0]}') ON CONFLICT DO NOTHING"
        )
        con.commit()
    cur.close()
    con.close()


def ingest_by_facet_query(database: Path, facets_by_project: dict[str, list[str]]):
    """
    Create a database by making a faceted search.

    Parameters
    ----------
    database
        The full path to the database file.
    facets_by_project
        A dictionary whose keys are project identifiers that resolve to a list
        of facets to include in the database as collections.

    Note
    ----
    For the moment we will harvest the CV by hard-coding the collections per
    project and then using a facet query to populate a list of terms to ingest.
    This allows us to include projects which have no formal CV repository. Later
    we may consider creating another ingest routine that reads the json files
    directly.
    """
    for project, facets in facets_by_project.items():
        url = f"https://esgf-node.ornl.gov/esgf-1-5-bridge/?project={project}&limit=0&facets={','.join(facets)}"
        resp = requests.get(url)
        resp.raise_for_status()
        create_cv_universe(
            database,
            [
                (term, collection, project)
                for collection, terms in resp.json()["facet_counts"][
                    "facet_fields"
                ].items()
                for term in terms[::2]
            ],
        )


def ingest_by_esgvoc(database: Path):
    raise NotImplementedError()
