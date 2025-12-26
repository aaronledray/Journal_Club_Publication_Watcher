import time
from Bio import Entrez
from urllib.error import HTTPError






#############################
# C.2: PubMed Fetchers
#############################


# Fetch relevant PMIDs:
def get_pmids(combined_query: str):
    """
    Take in a sql query and search pubmed using Entrez.esearch
    Return PMIDs
    """
    try:
        handle = Entrez.esearch(db="pubmed", term=combined_query, retmax=100000)
        try:
            record = Entrez.read(handle, validate=False)
        except Exception as ex:
            print(f"Entrez.read error. Error reading XML for query {combined_query}: {ex}")
            return []  # Skip this iteration and return an empty list
        pmids = record.get("IdList", [])
        return pmids
    except HTTPError as e:
        print(f"Entrez.esearch error. Error retrieving XML for query {combined_query}: {e}")
        return []  # Skip this iteration and return an empty list





def build_keyword_query(keyword: str, start_date: str, end_date: str, journals: list) -> str:
    """
    Build a PubMed query using a single keyword and date range.
    If journals are provided, they are combined with OR.
    """
    # Start with keyword and date range
    query = f'{keyword} AND ("{start_date}"[Date - Entry] : "{end_date}"[Date - Entry])'
    if journals and any(journals):
        # Create a clause that ORs all journal names
        journal_clause = " OR ".join([f'"{journal}"[Journal]' for journal in journals if journal])
        query += f' AND ({journal_clause})'
    return query





def build_orcid_query(orcid: str, start_date: str, end_date: str) -> str:
    """
    Build a PubMed query using an ORCID (author) and date range.
    """
    query = f'"{orcid}"[Author] AND ("{start_date}"[Date - Entry] : "{end_date}"[Date - Entry])'
    return query








# Function to actually FETCH get the paper, and handle erors:
def get_paper(pmid: str):
    """
    Use entrez.efetch to get paper metadata.
    """
    try:
        handle = Entrez.efetch(db="pubmed", id=pmid, rettype="medline", retmode="xml")
        paper = Entrez.read(handle, validate=False)
        time.sleep(1)
        return paper
    except HTTPError as e:
        if e.code == 500:  # If the error is an HTTP 500 error, retry
            print("HTTP Error 500 encountered. Retrying...")
            time.sleep(20)  # Wait for 20 seconds before retrying
            return get_paper(pmid)  # Retry the request
        elif e.code == 429:  # If the error is an HTTP 429 error, retry after 10 seconds
            print("HTTP Error 429 encountered. Too many requests. Retrying after 20 seconds...")
            time.sleep(20)  # Wait for 10 seconds before retrying
            return get_paper(pmid)  # Retry the request
        else:
            raise e  # If the error is not an HTTP 500 or 429 error, raise it
    except Exception as ex:
        print(f"An error occurred: {ex}")
        









def lookup_pubmed(config_file_dict: dict, start_end_date: tuple, mode: str = "keywords", attempt_number: int = 2) -> tuple:
    """
    Searches PubMed using:
    - Keyword + journal-based search (mode="keywords")
    - Author name-based search (mode="orcid") using config_file_dict["named_authors"]

    Returns:
        (keyword_papers, author_papers, keyword_frequency_dict)
    """
    import time
    from Bio import Entrez
    from urllib.error import HTTPError

    keyword_papers = []
    author_papers = []
    keyword_frequency_dict = {}

    email = config_file_dict['email']
    journals = config_file_dict.get('journals', [])
    keywords = config_file_dict.get('topics', [])
    named_authors = config_file_dict.get('named_authors', [])  # [{'orcid': ..., 'name': ...}, ...]

    start_date, end_date = start_end_date
    Entrez.email = email

    # --- 1. Keyword-based search ---
    if mode == "keywords" and keywords:
        print("Starting keyword-based PubMed search...")
        for keyword in keywords:
            query = build_keyword_query(keyword, start_date, end_date, journals)
            pmids = get_pmids(query)
            #print(f'PubMed query (keyword): {query}')
            keyword_frequency_dict[keyword] = len(pmids)

            for pmid in pmids:
                time.sleep(1)
                for _ in range(attempt_number):
                    try:
                        paper = get_paper(pmid)
                        paper["Source"] = "keyword"
                        keyword_papers.append(paper)
                        break
                    except HTTPError as e:
                        print(f"HTTPError: {e} for PMID {pmid}")
        if not keyword_papers:
            print("No papers found from keyword-based search.")

    # --- 2. Author name-based search ---
    elif mode == "orcid" and named_authors:
        print("Starting author-name-based PubMed search...")
        for author in named_authors:
            name = author.get("name")
            if not name:
                continue
            query = f'{name} [Author] AND ("{start_date}"[Date - Entry] : "{end_date}"[Date - Entry])'
            
            
            print(f'PubMed query (kauthor): {query}')
            pmids = get_pmids(query)
            
            print(pmids)



            for pmid in pmids:
                time.sleep(1)
                for _ in range(attempt_number):
                    try:
                        paper = get_paper(pmid)
                        paper["Source"] = "pubmed_author"
                        author_papers.append(paper)
                        break
                    except HTTPError as e:
                        print(f"HTTPError: {e} for PMID {pmid}")
        if not author_papers:
            print("No papers found from author-name-based search.")

    # --- Return ---
    return keyword_papers, author_papers, keyword_frequency_dict




