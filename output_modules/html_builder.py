"""
HTML dashboard builder for the Journal Lookup Tool.
Creates interactive HTML dashboards with DataTables and dark/light mode support.
"""

import json
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Tuple


def make_json_safe(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable format.
    
    Args:
        obj: Object to convert
        
    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, tuple):
        return [make_json_safe(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Convert custom objects to dictionaries
        return make_json_safe(obj.__dict__)
    elif hasattr(obj, 'value') and hasattr(obj, 'attributes'):
        # Handle special objects with value and attributes
        return {
            'value': str(obj.value),
            'attributes': make_json_safe(getattr(obj, 'attributes', {}))
        }
    else:
        # Try to convert to string for non-serializable objects
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


def safe_date_str(date: Any) -> str:
    """
    Safely convert date object to string.
    
    Args:
        date: Date object in various formats
        
    Returns:
        Formatted date string
    """
    if isinstance(date, dict):
        y = date.get('Year', '')
        m = date.get('Month', '')
        d = date.get('Day', '')
        return f"{y}/{m}/{d}" if y and m and d else "N/A"
    elif isinstance(date, str):
        return date
    elif isinstance(date, list):
        try:
            parts = date[0] if isinstance(date[0], list) else date
            return "/".join(str(p) for p in parts)
        except Exception:
            return "N/A"
    return "N/A"


def safe_authors(authors: Any) -> List[str]:
    """
    Safely convert authors to list of strings.
    
    Args:
        authors: Authors in various formats
        
    Returns:
        List of author names
    """
    if isinstance(authors, list):
        return [str(author) for author in authors if author]
    elif isinstance(authors, str):
        return [authors]
    return []


def safe_link(link: Any) -> str:
    """
    Safely extract link from various formats.
    
    Args:
        link: Link in various formats
        
    Returns:
        Link string or "N/A"
    """
    if isinstance(link, str):
        return link
    elif isinstance(link, list) and link:
        return str(link[0])
    elif hasattr(link, 'value'):
        return str(link.value)
    return "N/A"


def get_table_types(components: List[Dict[str, Any]]) -> List[str]:
    """
    Get unique paper source types from components.
    
    Args:
        components: List of paper components
        
    Returns:
        Sorted list of unique source types
    """
    types = set(comp.get("Source", "unknown") for comp in components)
    # Define preferred order
    order = ["keyword", "pubmed_author", "crossref", "orcid"]
    sorted_types = []
    
    for preferred in order:
        if preferred in types:
            sorted_types.append(preferred)
            types.remove(preferred)
    
    # Add any remaining types
    sorted_types.extend(sorted(types))
    return sorted_types


def get_source_label(source: str) -> str:
    """
    Get display label for paper source.
    
    Args:
        source: Source identifier
        
    Returns:
        Human-readable label
    """
    label_lookup = {
        "keyword": "Keyword-Based Results",
        "orcid": "Author-Based Results (ORCID)",
        "pubmed_author": "Author-Based Results (PubMed)",
        "crossref": "Author-Based Results (CrossRef)"
    }
    return label_lookup.get(source, f"{source.capitalize()} Results")


def write_html_head(f, title: str = "Journal Lookup Dashboard") -> None:
    """Write HTML head section with styles and external libraries."""
    f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
  <link rel="stylesheet" href="https://cdn.datatables.net/colreorder/1.6.2/css/colReorder.dataTables.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  <style>
    :root {{
      --bg-color: #ffffff;
      --text-color: #333333;
      --border-color: #dddddd;
      --header-bg: #f8f9fa;
      --link-color: #007bff;
      --hover-bg: #f5f5f5;
    }}

    [data-theme="dark"] {{
      --bg-color: #121212;
      --text-color: #e0e0e0;
      --border-color: #333333;
      --header-bg: #1e1e1e;
      --link-color: #4dabf7;
      --hover-bg: #2a2a2a;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 0;
      padding: 20px;
      background-color: var(--bg-color);
      color: var(--text-color);
      line-height: 1.6;
      transition: background-color 0.3s, color 0.3s;
    }}

    .header {{
      background: var(--header-bg);
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 30px;
      border: 1px solid var(--border-color);
    }}

    .header h1 {{
      margin: 0 0 15px 0;
      color: var(--text-color);
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .meta-info {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 15px;
      margin-top: 15px;
    }}

    .meta-item {{
      padding: 10px;
      background: var(--bg-color);
      border-radius: 4px;
      border: 1px solid var(--border-color);
    }}

    .controls {{
      margin-bottom: 20px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }}

    .btn {{
      padding: 8px 16px;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.3s;
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .btn-primary {{
      background-color: var(--link-color);
      color: white;
    }}

    .btn-primary:hover {{
      opacity: 0.9;
      transform: translateY(-1px);
    }}

    .section {{
      margin-bottom: 40px;
    }}

    .section h2 {{
      margin-top: 0;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border-color);
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .abstract-toggle {{
      cursor: pointer;
      color: var(--link-color);
      text-decoration: underline;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }}

    .abstract-toggle:hover {{
      opacity: 0.8;
    }}

    .abstract-text {{
      display: none;
      margin-top: 8px;
      padding: 10px;
      background: var(--hover-bg);
      border-radius: 4px;
      border-left: 3px solid var(--link-color);
      font-size: 0.9em;
      line-height: 1.5;
    }}

    td.expanding-cell {{
      max-width: 400px;
      word-wrap: break-word;
      white-space: normal;
      vertical-align: top;
      padding: 12px 8px;
    }}

    table.dataTable {{
      table-layout: auto !important;
      width: 100% !important;
      border-collapse: separate;
      border-spacing: 0;
    }}

    table.dataTable thead th {{
      background: var(--header-bg);
      border-bottom: 2px solid var(--border-color);
      padding: 12px 8px;
      font-weight: 600;
    }}

    table.dataTable tbody tr:hover {{
      background-color: var(--hover-bg);
    }}

    table.dataTable tbody td {{
      border-bottom: 1px solid var(--border-color);
    }}

    .dataTables_wrapper {{
      overflow-x: auto;
    }}

    .doi-link {{
      color: var(--link-color);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 3px;
    }}

    .doi-link:hover {{
      text-decoration: underline;
    }}

    .author-list {{
      margin: 0;
    }}

    .author-main {{
      font-weight: 500;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }}

    .stat-card {{
      background: var(--header-bg);
      padding: 15px;
      border-radius: 6px;
      text-align: center;
      border: 1px solid var(--border-color);
    }}

    .stat-number {{
      font-size: 2em;
      font-weight: bold;
      color: var(--link-color);
    }}

    .loading {{
      text-align: center;
      padding: 40px;
      color: var(--text-color);
    }}

    /* Statistics Modal */
    .statistics-modal {{
      display: none;
      position: fixed;
      z-index: 1000;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0,0,0,0.5);
    }}

    .statistics-content {{
      background-color: var(--bg-color);
      margin: 5% auto;
      padding: 20px;
      border-radius: 10px;
      width: 80%;
      max-width: 900px;
      max-height: 80vh;
      overflow-y: auto;
      position: relative;
    }}

    .statistics-close {{
      color: #aaa;
      float: right;
      font-size: 28px;
      font-weight: bold;
      cursor: pointer;
      position: absolute;
      right: 15px;
      top: 10px;
    }}

    .statistics-close:hover {{
      color: var(--text-color);
    }}

    .stats-section {{
      margin-bottom: 30px;
    }}

    .stats-section h3 {{
      color: var(--link-color);
      border-bottom: 2px solid var(--border-color);
      padding-bottom: 5px;
    }}

    .stats-grid-modal {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 15px;
      margin-top: 15px;
    }}

    .stats-item-modal {{
      background: var(--header-bg);
      padding: 15px;
      border-radius: 8px;
      border-left: 4px solid var(--link-color);
    }}

    .stats-item-modal strong {{
      color: var(--link-color);
      font-size: 1.2em;
    }}

    .top-list {{
      list-style: none;
      padding: 0;
    }}

    .top-list li {{
      padding: 8px;
      margin: 5px 0;
      background: var(--hover-bg);
      border-radius: 4px;
      display: flex;
      justify-content: space-between;
    }}

    .top-list li:nth-child(-n+3) {{
      border-left: 4px solid var(--link-color);
    }}

    @media (max-width: 768px) {{
      body {{ padding: 10px; }}
      .meta-info {{ grid-template-columns: 1fr; }}
      .controls {{ justify-content: center; }}
      table.dataTable {{ font-size: 0.9em; }}
    }}
  </style>
</head>
<body data-theme="light">
""")


def write_html_header(f, config_file_dict: Dict[str, Any], start_end_date: Tuple[str, str], components: List[Dict[str, Any]]) -> None:
    """Write the dashboard header with metadata and statistics."""
    start_date, end_date = start_end_date
    
    # Calculate statistics
    total_papers = len(components)
    source_counts = {}
    for comp in components:
        source = comp.get('Source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    f.write(f"""
  <div class="header">
    <h1>
      <i class="fas fa-microscope"></i>
      Journal Lookup Dashboard
    </h1>
    
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number">{total_papers}</div>
        <div>Total Papers</div>
      </div>
""")
    
    for source, count in source_counts.items():
        icon = {
            'keyword': 'fas fa-search',
            'crossref': 'fas fa-users',
            'pubmed_author': 'fas fa-user-md',
            'orcid': 'fas fa-id-card'
        }.get(source, 'fas fa-file')
        
        f.write(f"""
      <div class="stat-card">
        <div class="stat-number">{count}</div>
        <div><i class="{icon}"></i> {get_source_label(source)}</div>
      </div>
""")
    
    f.write("""
    </div>
    
    <div class="meta-info">
      <div class="meta-item">
        <strong><i class="fas fa-clock"></i> Report generated:</strong><br>
        {}</div>
      <div class="meta-item">
        <strong><i class="fas fa-calendar"></i> Date range:</strong><br>
        {} to {}</div>
      <div class="meta-item">
        <strong><i class="fas fa-envelope"></i> User email:</strong><br>
        {}</div>
    </div>
""".format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        start_date, end_date,
        config_file_dict.get('email', 'Not specified')
    ))

    # Configuration details
    if config_file_dict.get('journals'):
        journals_str = ", ".join(config_file_dict['journals'])
        
        f.write(f"""
    <div class="meta-info">
      <div class="meta-item">
        <strong><i class="fas fa-book"></i> Monitored Journals:</strong><br>
        {journals_str}</div>
""")
    
    if config_file_dict.get('topics'):
        topics_str = ", ".join(config_file_dict['topics'])
        
        f.write(f"""
      <div class="meta-item">
        <strong><i class="fas fa-tags"></i> Keywords:</strong><br>
        {topics_str}</div>
""")
    
    if config_file_dict.get('named_authors'):
        authors_info = []
        for author in config_file_dict['named_authors']:
            name = author.get('name', 'Unknown')
            orcid = author.get('orcid', '')
            authors_info.append(f"{name} ({orcid})")
        
        authors_str = ", ".join(authors_info)
        
        f.write(f"""
      <div class="meta-item">
        <strong><i class="fas fa-user-friends"></i> Tracked Authors:</strong><br>
        {authors_str}</div>
""")
    
    f.write("""
    </div>
  </div>
  
  <div class="controls">
    <button class="btn btn-primary" onclick="toggleTheme()">
      <i class="fas fa-moon"></i>
      <span id="theme-text">Dark Mode</span>
    </button>
    <button class="btn btn-primary" onclick="exportData()">
      <i class="fas fa-download"></i>
      Export Data
    </button>
    <button class="btn btn-primary" onclick="showStatistics()">
      <i class="fas fa-chart-bar"></i>
      Statistics
    </button>
  </div>

  <!-- Statistics Modal -->
  <div id="statisticsModal" class="statistics-modal">
    <div class="statistics-content">
      <span class="statistics-close" onclick="closeStatistics()">&times;</span>
      <h2><i class="fas fa-chart-bar"></i> Research Statistics</h2>
      <div id="statisticsContent">
        <!-- Content will be populated by JavaScript -->
      </div>
    </div>
  </div>
""")


def write_table_section(f, components: List[Dict[str, Any]], paper_type: str) -> None:
    """Write a table section for a specific paper type."""
    if not any(comp.get("Source") == paper_type for comp in components):
        return
    
    label = get_source_label(paper_type)
    table_id = f"papersTable_{paper_type}"
    
    # Count papers for this type
    type_count = sum(1 for comp in components if comp.get("Source") == paper_type)
    
    f.write(f"""
  <div class="section">
    <h2>
      <i class="fas fa-table"></i>
      {label}
      <span style="font-size: 0.7em; font-weight: normal; color: var(--text-color); opacity: 0.7;">
        ({type_count} papers)
      </span>
    </h2>
    
    <table id="{table_id}" class="display">
      <thead>
        <tr>
          <th><i class="fas fa-file-alt"></i> Title</th>
          <th><i class="fas fa-align-left"></i> Abstract</th>
          <th><i class="fas fa-book-open"></i> Journal</th>
          <th><i class="fas fa-calendar-alt"></i> Date</th>
          <th><i class="fas fa-link"></i> DOI</th>
          <th><i class="fas fa-users"></i> Authors (first & last)</th>
          <th><i class="fas fa-university"></i> Institutions</th>
        </tr>
      </thead>
      <tbody>
""")
    
    for comp in components:
        if comp.get("Source") != paper_type:
            continue
        
        title = comp.get("Title", "N/A")
        abstract = comp.get("Abstract", "N/A")
        journal = comp.get("Journal", "N/A")
        authors_list = safe_authors(comp.get("Authors", []))
        institutions_list = comp.get("Institution", [])
        institutions = ", ".join(institutions_list) if isinstance(institutions_list, list) else "N/A"
        date_str = safe_date_str(comp.get("Date"))
        doi = safe_link(comp.get("Link"))
        
        # Create unique IDs for expandable content
        title_hash = abs(hash(title)) % 10000
        abstract_id = f"{paper_type}_abstract_{title_hash}"
        inst_id = f"{paper_type}_inst_{title_hash}"
        author_id = f"{paper_type}_authors_{title_hash}"
        
        # Format DOI link
        if doi and doi != "N/A" and "doi.org" not in doi:
            doi_link = f'<a href="https://doi.org/{doi}" target="_blank" class="doi-link"><i class="fas fa-external-link-alt"></i> {doi}</a>'
        elif doi and doi != "N/A":
            doi_link = f'<a href="{doi}" target="_blank" class="doi-link"><i class="fas fa-external-link-alt"></i> {doi}</a>'
        else:
            doi_link = "N/A"
        
        # Format authors
        if authors_list:
            first_author = authors_list[0]
            if len(authors_list) == 1:
                author_display = f'<span class="author-main">{first_author}</span>'
            elif len(authors_list) == 2:
                author_display = f'<span class="author-main">{first_author}</span>, {authors_list[1]}'
            else:
                last_author = authors_list[-1]
                middle_authors = ", ".join(authors_list[1:-1])
                author_button = f'<span class="abstract-toggle" onclick="toggleAbstract(\'{author_id}\')"> (+{len(authors_list)-2} more)</span>'
                author_block = f'<div id="{author_id}" class="abstract-text">{middle_authors}</div>'
                author_display = f'<span class="author-main">{first_author}</span>, {last_author}{author_button}{author_block}'
        else:
            author_display = "N/A"
        
        f.write(f"""
        <tr>
          <td class="expanding-cell">{title}</td>
          <td class="expanding-cell">
            <span class="abstract-toggle" onclick="toggleAbstract('{abstract_id}')">
              <i class="fas fa-eye"></i> View Abstract
            </span>
            <div id="{abstract_id}" class="abstract-text">{abstract}</div>
          </td>
          <td class="expanding-cell">{journal}</td>
          <td>{date_str}</td>
          <td>{doi_link}</td>
          <td class="expanding-cell author-list">{author_display}</td>
          <td class="expanding-cell">
            <span class="abstract-toggle" onclick="toggleAbstract('{inst_id}')">
              <i class="fas fa-building"></i> View Institutions
            </span>
            <div id="{inst_id}" class="abstract-text">{institutions}</div>
          </td>
        </tr>
""")
    
    f.write("""
      </tbody>
    </table>
  </div>
""")


def write_html_scripts(f) -> None:
    """Write JavaScript for interactivity."""
    f.write("""
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/colreorder/1.6.2/js/dataTables.colReorder.min.js"></script>
<script>
  $(document).ready(function () {
    // Initialize DataTables
    $('table.display').DataTable({ 
      pageLength: 10,
      lengthChange: true,
      responsive: false,
      scrollX: true,
      scrollCollapse: true,
      colReorder: true,
      order: [[3, 'desc']], // Sort by date by default
      columnDefs: [
        { targets: [1, 5, 6], orderable: false }, // Disable sorting for expandable columns
        { targets: 0, width: '200px' },
        { targets: 1, width: '350px' }, // Abstract wider
        { targets: 2, width: '180px' },
        { targets: 3, width: '100px' },
        { targets: 4, width: '120px' },
        { targets: 5, width: '200px' },
        { targets: 6, width: '200px' }
      ],
      fixedColumns: false,
      autoWidth: false
    });
  });

  function toggleAbstract(id) {
    var el = document.getElementById(id);
    if (el) {
      var isVisible = el.style.display === 'block';
      el.style.display = isVisible ? 'none' : 'block';
      
      // Adjust DataTable layout
      const table = el.closest('table');
      if (table && $.fn.dataTable.isDataTable(table)) {
        setTimeout(() => {
          $(table).DataTable().columns.adjust().draw();
        }, 100);
      }
    }
  }

  function toggleTheme() {
    var body = document.body;
    var themeText = document.getElementById('theme-text');
    var moonIcon = themeText.previousElementSibling;
    
    if (body.getAttribute('data-theme') === 'light') {
      body.setAttribute('data-theme', 'dark');
      themeText.textContent = 'Light Mode';
      moonIcon.className = 'fas fa-sun';
    } else {
      body.setAttribute('data-theme', 'light');
      themeText.textContent = 'Dark Mode';
      moonIcon.className = 'fas fa-moon';
    }
  }
  
  function exportData() {
    // Export current view data as CSV
    var tables = document.querySelectorAll('table.display');
    var csvContent = "data:text/csv;charset=utf-8,";
    
    tables.forEach((table, index) => {
      if (index > 0) csvContent += "\\n\\n";
      
      // Add table header
      var headerCells = table.querySelectorAll('thead th');
      var headerRow = Array.from(headerCells).map(cell => 
        '"' + cell.textContent.trim().replace(/"/g, '""') + '"'
      ).join(',');
      csvContent += headerRow + "\\n";
      
      // Add table rows
      var bodyRows = table.querySelectorAll('tbody tr');
      bodyRows.forEach(row => {
        var cells = row.querySelectorAll('td');
        var rowData = Array.from(cells).map(cell => {
          var text = cell.textContent.trim();
          // Remove button text and extra whitespace
          text = text.replace(/View Abstract|View Institutions|\\+\\d+ more/g, '').trim();
          return '"' + text.replace(/"/g, '""') + '"';
        }).join(',');
        csvContent += rowData + "\\n";
      });
    });
    
    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "journal_lookup_results.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  function showStatistics() {
    const modal = document.getElementById('statisticsModal');
    const content = document.getElementById('statisticsContent');
    
    // Generate statistics from current data
    const stats = generateStatistics();
    
    content.innerHTML = `
      <div class="stats-section">
        <h3><i class="fas fa-chart-pie"></i> Overview</h3>
        <div class="stats-grid-modal">
          <div class="stats-item-modal">
            <strong>${stats.totalPapers}</strong><br>
            Total Papers
          </div>
          <div class="stats-item-modal">
            <strong>${stats.totalJournals}</strong><br>
            Unique Journals
          </div>
          <div class="stats-item-modal">
            <strong>${stats.totalAuthors}</strong><br>
            Unique Authors
          </div>
          <div class="stats-item-modal">
            <strong>${stats.averageAuthorsPerPaper.toFixed(1)}</strong><br>
            Avg Authors/Paper
          </div>
        </div>
      </div>

      <div class="stats-section">
        <h3><i class="fas fa-trophy"></i> Top Journals</h3>
        <ul class="top-list">
          ${stats.topJournals.slice(0, 10).map((item, index) => 
            `<li><span>${index + 1}. ${item.name}</span><strong>${item.count}</strong></li>`
          ).join('')}
        </ul>
      </div>

      <div class="stats-section">
        <h3><i class="fas fa-user-friends"></i> Most Prolific Authors</h3>
        <ul class="top-list">
          ${stats.topAuthors.slice(0, 10).map((item, index) => 
            `<li><span>${index + 1}. ${item.name}</span><strong>${item.count}</strong></li>`
          ).join('')}
        </ul>
      </div>

      <div class="stats-section">
        <h3><i class="fas fa-search"></i> Search Source Breakdown</h3>
        <div class="stats-grid-modal">
          ${Object.entries(stats.sourceBreakdown).map(([source, count]) => `
            <div class="stats-item-modal">
              <strong>${count}</strong><br>
              ${source.charAt(0).toUpperCase() + source.slice(1)} Results
            </div>
          `).join('')}
        </div>
      </div>

      <div class="stats-section">
        <h3><i class="fas fa-calendar-alt"></i> Publication Timeline</h3>
        <div class="stats-grid-modal">
          ${Object.entries(stats.yearBreakdown).slice(0, 6).map(([year, count]) => `
            <div class="stats-item-modal">
              <strong>${count}</strong><br>
              ${year}
            </div>
          `).join('')}
        </div>
      </div>
    `;
    
    modal.style.display = 'block';
  }

  function closeStatistics() {
    document.getElementById('statisticsModal').style.display = 'none';
  }

  function generateStatistics() {
    const tables = document.querySelectorAll('table.display tbody tr');
    let totalPapers = 0;
    let journals = {};
    let authors = {};
    let sources = {};
    let years = {};
    let totalAuthorCount = 0;

    tables.forEach(row => {
      const cells = row.querySelectorAll('td');
      if (cells.length < 6) return;

      totalPapers++;

      // Extract journal
      const journal = cells[2].textContent.trim();
      if (journal && journal !== 'N/A') {
        journals[journal] = (journals[journal] || 0) + 1;
      }

      // Extract authors
      const authorCell = cells[5];
      const authorText = authorCell.textContent.trim();
      if (authorText && authorText !== 'N/A') {
        const authorList = authorText.split(',').map(a => a.trim()).filter(a => 
          a && !a.includes('(+') && !a.includes('more)')
        );
        totalAuthorCount += authorList.length;
        
        authorList.forEach(author => {
          if (author.length > 3) {
            authors[author] = (authors[author] || 0) + 1;
          }
        });
      }

      // Extract year from date
      const dateCell = cells[3].textContent.trim();
      const yearMatch = dateCell.match(/(\\d{4})/);
      if (yearMatch) {
        const year = yearMatch[1];
        years[year] = (years[year] || 0) + 1;
      }

      // Determine source from table ID
      const table = row.closest('table');
      if (table) {
        const tableId = table.id || '';
        if (tableId.includes('keyword')) {
          sources['keyword'] = (sources['keyword'] || 0) + 1;
        } else if (tableId.includes('crossref')) {
          sources['crossref'] = (sources['crossref'] || 0) + 1;
        } else if (tableId.includes('pubmed')) {
          sources['pubmed_author'] = (sources['pubmed_author'] || 0) + 1;
        } else {
          sources['other'] = (sources['other'] || 0) + 1;
        }
      }
    });

    const sortByCount = (obj) => Object.entries(obj)
      .map(([name, count]) => ({name, count}))
      .sort((a, b) => b.count - a.count);

    return {
      totalPapers,
      totalJournals: Object.keys(journals).length,
      totalAuthors: Object.keys(authors).length,
      averageAuthorsPerPaper: totalPapers > 0 ? totalAuthorCount / totalPapers : 0,
      topJournals: sortByCount(journals),
      topAuthors: sortByCount(authors),
      sourceBreakdown: sources,
      yearBreakdown: Object.fromEntries(
        Object.entries(years).sort(([a], [b]) => b.localeCompare(a))
      )
    };
  }

  // Close modal when clicking outside
  window.onclick = function(event) {
    const modal = document.getElementById('statisticsModal');
    if (event.target === modal) {
      closeStatistics();
    }
  }
</script>
</body>
</html>
""")


def write_html_dashboard(
    start_end_date: Tuple[str, str],
    config_file_dict: Dict[str, Any],
    components: List[Dict[str, Any]],
    keyword_frequency_dict: Dict[str, int],
    html_name: str = "publications.html",
    json_dump_path: str = "results.json",
    auto_mode: bool = False
) -> None:
    """
    Write an interactive HTML dashboard with the search results.
    
    Args:
        start_end_date: Date range tuple
        config_file_dict: Configuration dictionary
        components: List of paper components
        keyword_frequency_dict: Keyword frequency data
        html_name: Output HTML filename
        json_dump_path: Output JSON filename
        auto_mode: Whether running in automatic mode
    """
    # Check if file exists and get permission if not in auto mode
    if Path(html_name).exists() and not auto_mode:
        response = input(f"{html_name} already exists. Overwrite? (y/n): ").strip().lower()
        if response not in ['y', 'yes']:
            print("HTML dashboard creation cancelled.")
            return
    
    # Save JSON data
    data_for_json = {
        "start_end_date": [str(d) for d in start_end_date],
        "config_file_dict": make_json_safe(config_file_dict),
        "components": make_json_safe(components),
        "keyword_frequency_dict": make_json_safe(keyword_frequency_dict),
        "generated_at": datetime.now().isoformat()
    }
    
    with open(json_dump_path, 'w', encoding='utf-8') as jf:
        json.dump(data_for_json, jf, indent=2)
    
    # Write HTML dashboard
    with open(html_name, 'w', encoding='utf-8') as f:
        write_html_head(f)
        write_html_header(f, config_file_dict, start_end_date, components)
        
        # Write table sections for each paper type
        for paper_type in get_table_types(components):
            write_table_section(f, components, paper_type)
        
        write_html_scripts(f)
    
    print(f"Interactive HTML dashboard written to: {html_name}")
    print(f"Data saved to: {json_dump_path}")


# Legacy function name for backward compatibility
write_html_file2 = write_html_dashboard


if __name__ == "__main__":
    # Test the HTML builder
    print("Testing HTML dashboard builder...")
    
    # Sample data
    sample_components = [
        {
            'Title': 'Machine Learning in Drug Discovery',
            'Authors': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Journal': 'Nature Biotechnology',
            'Date': '2024/01/15',
            'Abstract': 'This paper explores the application of machine learning techniques in drug discovery processes.',
            'Source': 'keyword',
            'Link': '10.1038/s41587-024-0001-1',
            'Institution': ['MIT', 'Harvard Medical School']
        },
        {
            'Title': 'CRISPR Applications in Gene Therapy',
            'Authors': ['Alice Wilson'],
            'Journal': 'Cell',
            'Date': '2024/02/20',
            'Abstract': 'A comprehensive review of CRISPR-Cas9 applications in therapeutic gene editing.',
            'Source': 'crossref',
            'Link': 'https://doi.org/10.1016/j.cell.2024.001',
            'Institution': ['Stanford University']
        }
    ]
    
    sample_config = {
        'email': 'researcher@university.edu',
        'journals': ['Nature', 'Science', 'Cell'],
        'topics': ['machine learning', 'CRISPR', 'gene therapy'],
        'named_authors': [
            {'name': 'John Doe', 'orcid': '0000-0000-0000-0001'},
            {'name': 'Jane Smith', 'orcid': '0000-0000-0000-0002'}
        ]
    }
    
    # Test dashboard creation
    write_html_dashboard(
        start_end_date=('2024/01/01', '2024/12/31'),
        config_file_dict=sample_config,
        components=sample_components,
        keyword_frequency_dict={'machine learning': 1, 'CRISPR': 1, 'gene therapy': 1},
        html_name='test_dashboard.html',
        json_dump_path='test_results.json',
        auto_mode=True
    )
    
    print("HTML dashboard builder test completed.")