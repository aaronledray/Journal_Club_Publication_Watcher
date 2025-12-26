# import os





import os

def write_txt_file(start_end_date: tuple,
                   config_file_dict: dict,
                   components_keyword: list,
                   components_orcid: list,
                   keyword_frequency_dict: dict,
                   txt_name: str = '0_publications.txt',
                   auto_mode: bool = False):
    """
    Writes a raw .txt file showing both keyword and ORCID result sections (if present).
    """
    if os.path.exists(txt_name):
        if auto_mode:
            print(f"{txt_name} already exists. Auto mode enabled: overwriting automatically.")
        else:
            response = input(f"{txt_name} already exists. Would you like to overwrite it? (y)es/(n)o: ")
            if response.lower() not in ['y', 'yes']:
                print("Operation cancelled. Please rename or delete the existing file.")
                return

    if not components_keyword and not components_orcid:
        print("No results found to write. Skipping text file generation.")
        return

    with open(txt_name, 'w') as f:
        version = config_file_dict.get('version', '1.0')
        f.write(f"Journal Lookup Tool v{version}\n")
        f.write("By AP Ledray\n")
        f.write("Contact: aaronledray@gmail.com\n\n")

        email = config_file_dict['email']
        journals = config_file_dict.get('journals', [])
        topics = config_file_dict.get('topics', [])
        authors = config_file_dict.get('authors', [])
        start_date, end_date = start_end_date

        f.write("=== Query Information ===\n")
        f.write(f"Username: {email}\n")
        f.write(f"Query start date: {start_date}\n")
        f.write(f"Query end date: {end_date}\n\n")
        f.write("Journals:\n" + "\n".join(f"- {j}" for j in journals) + "\n")
        if authors:
            f.write("Tracked ORCIDs:\n" + "\n".join(f"- {a}" for a in authors) + "\n")
        f.write("\n")
        f.write("Keywords:\n" + ", ".join(topics) + "\n\n")

        # Keyword section
        if components_keyword:
            f.write("=== Results from Keyword + Journal Queries ===\n\n")

            # Journal summary for keyword results
            journal_data = {}
            for component in components_keyword:
                if "Journal" in component:
                    journal = component["Journal"]
                    journal_data[journal] = journal_data.get(journal, 0) + 1

            if journal_data:
                f.write("Journals Found:\n")
                for journal, count in journal_data.items():
                    f.write(f"{journal}: {count}\n")
                f.write("\n")

            f.write("Keyword Hit Statistics:\n")
            for keyword, hits in keyword_frequency_dict.items():
                if hits > 0:
                    f.write(f"{keyword}: {hits}\n")
            f.write("\n")

            for component in components_keyword:
                write_paper_block(f, component)

        # ORCID section
        if components_orcid:
            f.write("=== Results from ORCID Watchlist Queries ===\n\n")
            for component in components_orcid:
                write_paper_block(f, component)

    print(f"Text file '{txt_name}' generated successfully.")


def write_paper_block(f, component):
    """Helper to write a paper block to file"""
    f.write("Paper Details:\n")
    f.write(f"Title: {component.get('Title', 'N/A')}\n")
    f.write(f"Abstract: {component.get('Abstract', 'Not available')}\n")
    f.write(f"Journal: {component.get('Journal', 'Not available')}\n")

    if "Date" in component:
        date = component["Date"][0]
        if all(k in date for k in ("Year", "Month", "Day")):
            f.write(f"Publication Date: {date['Year']}/{date['Month']}/{date['Day']}\n")

    f.write(f"DOI: {component.get('Link', ['Not available'])[0]}\n")
    f.write("Authors: " + ", ".join(component.get("Authors", ['Not available'])) + "\n")
    f.write("Institutions: " + ", ".join(component.get("Institution", ['Not available'])) + "\n\n")
