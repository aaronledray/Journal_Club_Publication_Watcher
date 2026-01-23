#!/usr/bin/env python3
"""
Journal Club Publication Watcher

A tool for searching PubMed and CrossRef for relevant academic publications.
Generates PowerPoint slides, HTML dashboards, and text summaries for quick review.

See CHANGELOG.md for version history.
"""

import argparse
import json
import os
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple



from config.config_loader import load_config
from core.date_utils import ask_user_date
from core.paper_processor import process_papers, combine_components
from fetch_modules.crossref_client import lookup_crossref
from fetch_modules.pubmed_client import lookup_pubmed
from output_modules.file_writers import write_txt_file, write_json_file
from output_modules.html_builder import write_html_dashboard
from make_modules.pptx_maker import create_presentation
from utils.browser_utils import open_links_in_safari
from utils.display import print_opener, print_results_summary


VERSION = "3.6.0"
UPDATE_DATE = "20251226"



def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Journal lookup tool for academic research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --auto --mode keywords    # Auto mode, keywords only
  %(prog)s --mode authors           # Interactive mode, authors only
  %(prog)s                          # Interactive mode, both keywords and authors
        """
    )
    
    parser.add_argument(
        '--auto', 
        action='store_true', 
        help="Run in automatic (non-interactive) mode"
    )
    
    parser.add_argument(
        "--mode",
        choices=["both", "keywords", "authors"],
        default="both",
        help="Select search mode (default: both)"
    )
    
    parser.add_argument(
        "--config-dir",
        default="config",
        help="Configuration directory path (default: config)"
    )
    
    parser.add_argument(
        "--output-dir", 
        default=".",
        help="Output directory for generated files (default: current directory)"
    )
    
    return parser.parse_args()


def search_publications(
    config: Dict, 
    date_range: Tuple[str, str], 
    mode: str
) -> Tuple[List, List, List, Dict]:
    """
    Search for publications based on configuration and mode.
    
    Returns:
        Tuple of (keyword_papers, pubmed_author_papers, crossref_papers, keyword_frequencies)
    """
    keyword_papers = []
    pubmed_author_papers = []
    crossref_papers = []
    keyword_frequencies = {kw: 0 for kw in config.get('topics', [])}
    
    # Keyword-based search
    if mode in ["keywords", "both"] and config.get('topics'):
        print('Searching PubMed by keywords...')
        keyword_papers, _, keyword_frequencies = lookup_pubmed(
            config_file_dict=config,
            start_end_date=date_range,
            mode="keywords"
        )
        print(f'   Found {len(keyword_papers)} keyword-based papers')
    
    # Author-based searches
    if mode in ["authors", "both"] and (config.get('orcids') or config.get('named_authors')):
        print('Searching by authors...')
        
        # PubMed author search (if you have this implemented)
        # if config.get('named_authors'):
        #     print('   Searching PubMed by author names...')
        #     _, pubmed_author_papers, _ = lookup_pubmed(
        #         config_file_dict=config,
        #         start_end_date=date_range,
        #         mode="authors"
        #     )
        
        # CrossRef ORCID search
        if config.get('orcids'):
            print('   Searching CrossRef by ORCIDs...')
            crossref_papers = lookup_crossref(
                orcids=config['orcids'],
                start_end_date=date_range
            )
            print(f'   Found {len(crossref_papers)} CrossRef papers')
    
    return keyword_papers, pubmed_author_papers, crossref_papers, keyword_frequencies


def generate_outputs(
    config: Dict,
    date_range: Tuple[str, str],
    components_keyword: List,
    components_orcid: List,
    keyword_frequencies: Dict,
    output_dir: str,
    auto_mode: bool
) -> None:
    """Generate all output files."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    components_all = components_keyword + components_orcid
    
    # Text file
    print('Writing text file...')
    write_txt_file(
        start_end_date=date_range,
        config_file_dict=config,
        components_keyword=components_keyword,
        components_orcid=components_orcid,
        keyword_frequency_dict=keyword_frequencies,
        txt_name=str(output_path / 'publications.txt'),
        auto_mode=auto_mode
    )
    
    # PowerPoint presentation
    print('Creating PowerPoint presentation...')
    create_presentation(
        start_end_date=date_range,
        config_file_dict=config,
        components_keyword=components_keyword,
        components_orcid=components_orcid,
        keyword_frequency_dict=keyword_frequencies,
        auto_mode=auto_mode,
        version=VERSION,
        output_path=str(output_path / 'publications.pptx')
    )
    
    # HTML dashboard
    print('Creating HTML dashboard...')
    html_path = output_path / 'publications.html'
    write_html_dashboard(
        start_end_date=date_range,
        config_file_dict=config,
        components=components_all,
        keyword_frequency_dict=keyword_frequencies,
        html_name=str(html_path),
        auto_mode=auto_mode
    )
    
    # JSON results
    print('Saving JSON results...')
    write_json_file(
        data={
            "start_end_date": date_range,
            "config_file_dict": config,
            "components": components_all,
            "keyword_frequency_dict": keyword_frequencies,
            "generated_at": datetime.now().isoformat(),
            "version": VERSION
        },
        filename=str(output_path / 'results.json')
    )
    
    # Open browser if not in auto mode
    if not auto_mode:
        print(' Opening dashboard in browser...')
        webbrowser.open(f'file://{html_path.resolve()}')


def main() -> None:
    """Main entry point."""
    args = parse_arguments()
    
    # Display header
    print_opener(VERSION, UPDATE_DATE)
    
    if args.auto:
        print(" Running in AUTO mode (non-interactive)")
    
    try:
        # Load configuration
        # print('  Loading configuration...')
        config, keyword_frequencies = load_config(args.config_dir)
        
        # Get date range
        date_range = ask_user_date(
            config['lookup_frequency'], 
            auto_mode=args.auto
        )
        
        # Search for publications
        print('Searching for publications...')
        keyword_papers, pubmed_author_papers, crossref_papers, keyword_frequencies = search_publications(
            config, date_range, args.mode
        )
        
        # Process papers into components
        print('Processing paper data...')
        components_keyword, components_orcid = process_papers(
            keyword_papers, pubmed_author_papers, crossref_papers
        )
        
        # Display results summary
        print_results_summary(components_keyword, components_orcid)
        
        if not (components_keyword or components_orcid):
            print("No papers found matching your criteria.")
            return
        
        # Generate outputs
        generate_outputs(
            config, date_range, components_keyword, components_orcid,
            keyword_frequencies, args.output_dir, args.auto
        )
        
        # Open links in browser
        if not args.auto:
            components_all = components_keyword + components_orcid
            open_links_in_safari(components_all, auto_mode=args.auto)
        
        print("Journal lookup completed successfully!")
        

        

        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f" Error: {e}")
        if not args.auto:
            raise


if __name__ == "__main__":
    main()