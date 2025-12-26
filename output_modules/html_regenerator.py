# output_modules/html_regenerator.py

import json
import argparse
import os
from datetime import datetime

def regenerate_html_from_json(json_path: str, output_html: str = "0_publications_regenerated.html"):
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    start_end_date = data.get("start_end_date", ["?", "?"])
    config_file_dict = data.get("config_file_dict", {})
    components = data.get("components", [])
    keyword_frequency_dict = data.get("keyword_frequency_dict", {})

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Journal Lookup Dashboard</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ width: 100%; }}
        .abstract-toggle {{ cursor: pointer; color: #337ab7; text-decoration: underline; }}
        .abstract-text {{ display: none; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>Journal Lookup Dashboard (Regenerated)</h1>
    <div>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Email:</strong> {config_file_dict.get("email", "N/A")}</p>
        <p><strong>Date Range:</strong> {start_end_date[0]} to {start_end_date[1]}</p>
        <p><strong>Journals:</strong> {", ".join(config_file_dict.get("journals", []))}</p>
        <p><strong>Keywords:</strong> {", ".join(config_file_dict.get("topics", []))}</p>
        <p><strong>Authors:</strong> {", ".join(config_file_dict.get("authors", []))}</p>
    </div>

    <table id="papersTable" class="display">
        <thead>
            <tr>
                <th>Title</th>
                <th>Abstract</th>
                <th>Journal</th>
                <th>Date</th>
                <th>DOI</th>
                <th>Authors</th>
                <th>Institutions</th>
            </tr>
        </thead>
        <tbody>
""")
        for comp in components:
            title = comp.get("Title", "N/A")
            abstract = comp.get("Abstract", "N/A")
            journal = comp.get("Journal", "N/A")
            authors = ", ".join(comp.get("Authors", [])) or "N/A"
            institutions = ", ".join(comp.get("Institution", [])) or "N/A"
            link = comp.get("Link", [""])[0]
            date = comp.get("Date", [{}])[0]
            date_str = f"{date.get('Year','')}/{date.get('Month','')}/{date.get('Day','')}" if all(k in date for k in ('Year','Month','Day')) else "N/A"
            doi_link = f'<a href="https://doi.org/{link}" target="_blank">{link}</a>' if link else "N/A"
            abstract_id = f"abstract_{hash(title)}"

            f.write(f"""
<tr>
    <td>{title}</td>
    <td>
        <span class="abstract-toggle" onclick="toggleAbstract('{abstract_id}')">Show/Hide Abstract</span>
        <div id="{abstract_id}" class="abstract-text">{abstract}</div>
    </td>
    <td>{journal}</td>
    <td>{date_str}</td>
    <td>{doi_link}</td>
    <td>{authors}</td>
    <td>{institutions}</td>
</tr>
""")

        f.write("""
        </tbody>
    </table>

<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script>
    $(document).ready(function () {
        $('#papersTable').DataTable({ pageLength: 10 });
    });
    function toggleAbstract(id) {
        var el = document.getElementById(id);
        el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }
</script>
</body>
</html>
""")

    print(f"✅ HTML regenerated and saved to: {output_html}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate HTML dashboard from saved JSON output.")
    parser.add_argument("--json", default="last_results.json", help="Path to saved JSON file")
    parser.add_argument("--out", default="0_publications_regenerated.html", help="Output HTML file path")
    args = parser.parse_args()

    regenerate_html_from_json(args.json, args.out)
