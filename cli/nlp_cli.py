#!/usr/bin/env python3
"""
Command-line interface for the NLP service.
"""

import argparse
import sys
import json
import logging
from typing import Optional, List, Set
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.nlp_service import NLPService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_known_words_from_file(file_path: str) -> Set[str]:
    """Load known words from a text file (one word per line)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            words = {line.strip().lower() for line in f if line.strip()}
        logger.info(f"Loaded {len(words)} known words from {file_path}")
        return words
    except FileNotFoundError:
        logger.error(f"Known words file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading known words file: {e}")
        sys.exit(1)


def process_text_from_file(nlp_service: NLPService, file_path: str, known_words: Optional[Set[str]] = None) -> str:
    """Process text from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return text
    except FileNotFoundError:
        logger.error(f"Text file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading text file: {e}")
        sys.exit(1)


def format_output(results: List[dict], output_format: str, output_file: Optional[str] = None):
    """Format and output results."""
    if output_format == "json":
        output_data = json.dumps(results, indent=2, ensure_ascii=False)
    elif output_format == "text":
        output_lines = []
        for result in results:
            output_lines.append(f"{result['lemma']} ({result['count']}): {', '.join(result['surface_forms'])}")
        output_data = "\n".join(output_lines)
    elif output_format == "csv":
        output_lines = ["lemma,count,surface_forms"]
        for result in results:
            surface_forms_str = ";".join(result['surface_forms'])
            output_lines.append(f"{result['lemma']},{result['count']},\"{surface_forms_str}\"")
        output_data = "\n".join(output_lines)
    else:
        logger.error(f"Unsupported output format: {output_format}")
        sys.exit(1)
    
    # Write to file or stdout
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_data)
            logger.info(f"Results written to {output_file}")
        except Exception as e:
            logger.error(f"Error writing to output file: {e}")
            sys.exit(1)
    else:
        print(output_data)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="NLP Service CLI - Extract unfamiliar noun lemmas from text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process text directly
  python cli/nlp_cli.py -t "The cat sat on the mat. Dogs are friendly animals."
  
  # Process text from file
  python cli/nlp_cli.py -f input.txt
  
  # Use known words from file
  python cli/nlp_cli.py -t "Some text here" --known-words known_words.txt
  
  # Output to JSON file
  python cli/nlp_cli.py -t "Some text" -o results.json --format json
  
  # Get only lemmas
  python cli/nlp_cli.py -t "Some text" --lemmas-only
  
  # Get only surface forms
  python cli/nlp_cli.py -t "Some text" --surface-forms-only
  
  # Get frequency mapping
  python cli/nlp_cli.py -t "Some text" --frequency-only
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-t", "--text",
        help="Text to process"
    )
    input_group.add_argument(
        "-f", "--file",
        help="File containing text to process"
    )
    
    # Known words options
    parser.add_argument(
        "--known-words",
        help="File containing known words (one per line) to filter out"
    )
    parser.add_argument(
        "--known-words-list",
        nargs="+",
        help="List of known words to filter out"
    )
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "text", "csv"],
        default="text",
        help="Output format (default: text)"
    )
    
    # Processing options
    parser.add_argument(
        "--lemmas-only",
        action="store_true",
        help="Return only lemmas (not full results)"
    )
    parser.add_argument(
        "--surface-forms-only",
        action="store_true",
        help="Return only surface forms (not full results)"
    )
    parser.add_argument(
        "--frequency-only",
        action="store_true",
        help="Return frequency mapping only"
    )
    
    # Model options
    parser.add_argument(
        "--model",
        help="spaCy model name (default: en_core_web_lg)"
    )
    
    # Verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize NLP service
    try:
        logger.info("Initializing NLP service...")
        nlp_service = NLPService(model_name=args.model)
        logger.info(f"NLP service initialized with model: {nlp_service.model_name}")
    except Exception as e:
        logger.error(f"Failed to initialize NLP service: {e}")
        sys.exit(1)
    
    # Get text to process
    if args.text:
        text = args.text
    else:
        text = process_text_from_file(nlp_service, args.file)
    
    # Load known words
    known_words = set()
    
    if args.known_words:
        known_words.update(load_known_words_from_file(args.known_words))
    
    if args.known_words_list:
        known_words.update(word.lower() for word in args.known_words_list)
    
    if known_words:
        logger.info(f"Using {len(known_words)} known words for filtering")
    
    # Process text
    try:
        logger.info(f"Processing text ({len(text)} characters)...")
        
        if args.lemmas_only:
            results = nlp_service.get_lemmas_only(text, known_words)
            if args.format == "json":
                output_data = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                output_data = "\n".join(results)
        
        elif args.surface_forms_only:
            results = nlp_service.get_surface_forms_only(text, known_words)
            if args.format == "json":
                output_data = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                output_data = "\n".join(results)
        
        elif args.frequency_only:
            results = nlp_service.get_word_frequency(text, known_words)
            if args.format == "json":
                output_data = json.dumps(results, indent=2, ensure_ascii=False)
            else:
                output_lines = [f"{lemma}: {count}" for lemma, count in results.items()]
                output_data = "\n".join(output_lines)
        
        else:
            # Full results
            results = nlp_service.process_text(text, known_words)
            format_output(results, args.format, args.output)
            return
        
        # Write output for simplified results
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(output_data)
                logger.info(f"Results written to {args.output}")
            except Exception as e:
                logger.error(f"Error writing to output file: {e}")
                sys.exit(1)
        else:
            print(output_data)
        
        logger.info(f"Processing complete. Found {len(results)} results.")
        
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 