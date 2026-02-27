import requests
import xml.etree.ElementTree as ET


def _connect_to_arxiv(arxiv_id):
    api_url = f"http://export.arxiv.org/api/query?search_query=id:{arxiv_id}"
    response = requests.get(api_url, timeout=20)
    if response.status_code != 200:
        raise ConnectionError(f"Unable to reach arXiv for id = {arxiv_id}")

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise ConnectionError(f"Unable to find arxiv paper with id = {arxiv_id}")

    title_el = entry.find("atom:title", ns)
    published_el = entry.find("atom:published", ns)
    author_els = entry.findall("atom:author/atom:name", ns)

    title = title_el.text.strip().replace("\n", " ") if title_el is not None else "UNKNOWN-TITLE"
    published = published_el.text if published_el is not None else ""
    year = int(published[:4]) if len(published) >= 4 and published[:4].isdigit() else None
    authors = [{"name": el.text.strip()} for el in author_els if el is not None and el.text]

    return {
        "paperId": None,
        "title": title,
        "authors": authors,
        "journal": {"name": "arXiv"},
        "venue": "arXiv",
        "year": year,
        "citationCount": None,
    }

def connect_to_s2(arxiv_id=None, doi=None):
    fields = ["year", "authors", "title", "journal", "venue", "citationCount"]
    if arxiv_id is not None:
        api_url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{arxiv_id}?fields={','.join(fields)}"
    elif doi is not None:
        api_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields={','.join(fields)}"
    else:
        raise ValueError("Either arxiv_id or doi should be provided.")

    response = requests.get(api_url, timeout=20)
    if response.status_code != 200:
        if arxiv_id is not None:
            return _connect_to_arxiv(arxiv_id)
        raise ConnectionError(f"Unable to find paper with DOI = {doi}")
    
    paper_data = response.json()
    return paper_data


def extract_metadata(paper_data):
    s2_id = paper_data.get("paperId")
    title = paper_data.get("title", "UNKNOWN-TITLE")
    authors_data = paper_data.get("authors") or []
    if len(authors_data) <= 2:
        authors = ", ".join([author["name"] for author in authors_data])
    else:
        authors = authors_data[0]["name"] + " et al"
    journal_data = paper_data.get("journal")
    if journal_data is not None:
        journal = journal_data.get("name")
        if journal is None:
            journal = paper_data["venue"]
    else:
        journal = "Working Paper"
    year = paper_data.get("year", "UNKNOWN-YEAR")
    citations = paper_data.get("citationCount")
    return s2_id, title, authors, journal, year, citations
