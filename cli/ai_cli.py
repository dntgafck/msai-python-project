#!/usr/bin/env python3
"""
Command-line interface for the AI service.
"""

import argparse
import sys
import json
import logging
import os
from typing import Optional, List
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.ai_service import AIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_lemmas_from_file(file_path: str) -> List[str]:
    """Load lemmas from a text file (one word per line)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lemmas = [line.strip().lower() for line in f if line.strip()]
        logger.info(f"Loaded {len(lemmas)} lemmas from {file_path}")
        return lemmas
    except FileNotFoundError:
        logger.error(f"Lemmas file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading lemmas file: {e}")
        sys.exit(1)


def format_output(definitions: List, output_format: str, output_file: Optional[str] = None):
    """Format and output results."""
    if output_format == "json":
        output_data = json.dumps([def_item.model_dump() for def_item in definitions], indent=2, ensure_ascii=False)
    elif output_format == "text":
        output_lines = []
        for def_item in definitions:
            output_lines.append(f"🇳🇱 {def_item.lemma.upper()}")
            output_lines.append(f"📖 Definition: {def_item.definition}")
            output_lines.append(f"💬 Example: {def_item.example}")
            output_lines.append(f"🌐 Translation: {def_item.english_translation}")
            output_lines.append(f"🏷️ Categories: {', '.join(def_item.category)}")
            output_lines.append("-" * 50)
        output_data = "\n".join(output_lines)
    elif output_format == "csv":
        output_lines = ["lemma,definition,example,english_translation,categories"]
        for def_item in definitions:
            categories_str = ";".join(def_item.category) if def_item.category else "general"
            output_lines.append(f"\"{def_item.lemma}\",\"{def_item.definition}\",\"{def_item.example}\",\"{def_item.english_translation}\",\"{categories_str}\"")
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
        description="AI Service CLI - Generate definitions for Dutch words",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate definitions for words directly
  python cli/ai_cli.py -w "handelaar" "kust" "markt"
  
  # Generate definitions from file
  python cli/ai_cli.py -f lemmas.txt
  
  # Output to JSON file
  python cli/ai_cli.py -w "handelaar" "kust" -o results.json --format json
  
  # Use custom batch size
  python cli/ai_cli.py -w "word1" "word2" "word3" --batch-size 5
  
  # Use different model
  python cli/ai_cli.py -w "handelaar" --model gpt-4o
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-w", "--words",
        nargs="+",
        help="Dutch words to generate definitions for"
    )
    input_group.add_argument(
        "-f", "--file",
        help="File containing Dutch words (one per line) to generate definitions for"
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
    
    # AI service options
    parser.add_argument(
        "--model",
        help="OpenAI model name (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Number of words to process per batch (default: 20)"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key (default: from OPENAI_API_KEY environment variable)"
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
    
    # Check for API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --api-key")
        sys.exit(1)
    
    # Initialize AI service
    try:
        logger.info("Initializing AI service...")
        ai_service = AIService(
            api_key=api_key,
            model=args.model,
            batch_size=args.batch_size
        )
        logger.info(f"AI service initialized with model: {ai_service.model}")
    except Exception as e:
        logger.error(f"Failed to initialize AI service: {e}")
        sys.exit(1)
    
    # Get lemmas to process
    if args.words:
        lemmas = [word.lower().strip() for word in args.words]
    else:
        lemmas = load_lemmas_from_file(args.file)
    
    if not lemmas:
        logger.error("No lemmas provided")
        sys.exit(1)
    
    logger.info(f"Processing {len(lemmas)} lemmas: {lemmas}")
    
    # Generate definitions
    try:
        logger.info("Generating definitions...")
        definitions = ai_service.generate_definitions(lemmas)
        
        logger.info(f"Successfully generated {len(definitions)} definitions")
        
        # Format and output results
        format_output(definitions, args.format, args.output)
        
        logger.info("Processing complete.")
        
    except Exception as e:
        logger.error(f"Error generating definitions: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 