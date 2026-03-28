"""
chemistry_tools.py

Real-world API wrappers for ChemVille agents. Each function accepts a plain
string query and returns a plain string result suitable for injecting into an
agent's associative memory. All requests have a 5-second timeout and return a
descriptive error string on failure rather than raising exceptions.
"""
import urllib.request
import urllib.parse
import json


def search_pubchem(compound_name: str) -> str:
    """Look up chemical properties for a compound on PubChem.

    Returns molecular formula, canonical SMILES, InChIKey, and molecular
    weight as a single descriptive string.
    """
    try:
        name_enc = urllib.parse.quote(compound_name.strip())
        url = (
            f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
            f"{name_enc}/property/MolecularFormula,CanonicalSMILES,"
            f"InChIKey,MolecularWeight/JSON"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ChemVille/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        props = data["PropertyTable"]["Properties"][0]
        return (
            f"PubChem result for '{compound_name}': "
            f"formula={props.get('MolecularFormula', 'N/A')}, "
            f"SMILES={props.get('CanonicalSMILES', 'N/A')}, "
            f"InChIKey={props.get('InChIKey', 'N/A')}, "
            f"MW={props.get('MolecularWeight', 'N/A')} g/mol"
        )
    except Exception as e:
        return f"PubChem search for '{compound_name}' failed: {e}"


def search_chembl(target_name: str) -> str:
    """Search ChEMBL for a drug target.

    Returns the top match's name, organism, target type, and ChEMBL ID.
    """
    try:
        query_enc = urllib.parse.quote(target_name.strip())
        url = (
            f"https://www.ebi.ac.uk/chembl/api/data/target/search"
            f"?q={query_enc}&format=json&limit=3"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ChemVille/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        targets = data.get("targets", [])
        if not targets:
            return f"ChEMBL search for '{target_name}': no targets found."
        results = []
        for t in targets[:3]:
            results.append(
                f"{t.get('pref_name', 'N/A')} "
                f"({t.get('organism', 'N/A')}, {t.get('target_type', 'N/A')}, "
                f"ChEMBL ID: {t.get('target_chembl_id', 'N/A')})"
            )
        return f"ChEMBL results for '{target_name}': " + "; ".join(results)
    except Exception as e:
        return f"ChEMBL search for '{target_name}' failed: {e}"


def search_literature(query: str) -> str:
    """Search Semantic Scholar for recent papers matching a query.

    Returns the top 3 results with title, year, first author, and abstract
    snippet (no API key required).
    """
    try:
        query_enc = urllib.parse.quote(query.strip())
        url = (
            f"https://api.semanticscholar.org/graph/v1/paper/search"
            f"?query={query_enc}&limit=3"
            f"&fields=title,year,authors,abstract"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "ChemVille/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        papers = data.get("data", [])
        if not papers:
            return f"Literature search for '{query}': no papers found."
        results = []
        for p in papers:
            first_author = (p.get("authors") or [{}])[0].get("name", "Unknown")
            abstract = (p.get("abstract") or "")[:150].replace("\n", " ")
            if len(p.get("abstract") or "") > 150:
                abstract += "..."
            results.append(
                f"\"{p.get('title', 'N/A')}\" "
                f"({first_author}, {p.get('year', 'N/A')}): {abstract}"
            )
        return f"Literature results for '{query}': " + " | ".join(results)
    except Exception as e:
        return f"Literature search for '{query}' failed: {e}"
