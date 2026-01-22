#!/usr/bin/env python3
"""
PDF Text Extraction Tool

This script extracts text from PDFs by automatically classifying them as scanned
or docx-based, then using the appropriate extractor (OCRExtractor for scanned,
PyMuPDF for docx-based).

Usage:
    pdm run python compare.py samples/
    pdm run python compare.py samples/sample.pdf
    pdm run python compare.py samples/ --output-dir results/
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from extractors import (
    ExtractionResult,
    PyMuPDFExtractor,
    OCRExtractor,
)
from utils.classify_pdf import classify_pdf


def run_extraction(
    pdf_path: Path,
    verbose: bool = True,
) -> list[ExtractionResult]:
    """
    Run appropriate extractor based on PDF classification.
    
    Args:
        pdf_path: Path to the PDF file
        verbose: Print progress
        
    Returns:
        List containing single extraction result
    """
    try:
        # Classify PDF
        pdf_type = classify_pdf(str(pdf_path))
        
        if verbose:
            print(f"  PDF type: {pdf_type}", end=" ", flush=True)
        
        # Select extractor based on classification
        if pdf_type == "docx":
            extractor = PyMuPDFExtractor()
        elif pdf_type == "scanned":
            extractor = OCRExtractor()
        else:
            raise ValueError(f"Unexpected PDF classification: {pdf_type}")
        
        if verbose:
            print(f"→ Using {extractor.name}...", end=" ", flush=True)
        
        # Run extraction with timing
        result = extractor.extract_with_timing(pdf_path)
        
        if verbose:
            if result.success:
                print(f"✓ ({result.execution_time_seconds:.2f}s, {result.word_count} words)")
            else:
                print(f"✗ ({result.error_message[:50]}...)")
        
        return [result]
        
    except Exception as e:
        # Return error result if classification or extraction fails
        error_result = ExtractionResult(
            extractor_name="ClassificationError",
            text="",
            success=False,
            error_message=str(e),
        )
        
        if verbose:
            print(f"✗ Error: {str(e)[:50]}...")
        
        return [error_result]


def generate_comparison_table(results: list[ExtractionResult]) -> str:
    """Generate a markdown comparison table."""
    lines = [
        "| Extractor | Success | Time (s) | Words | Chars | Lines |",
        "|-----------|---------|----------|-------|-------|-------|",
    ]
    
    for r in results:
        status = "✓" if r.success else "✗"
        lines.append(
            f"| {r.extractor_name} | {status} | {r.execution_time_seconds:.2f} | "
            f"{r.word_count} | {r.char_count} | {r.line_count} |"
        )
    
    return "\n".join(lines)


def save_results(
    pdf_path: Path,
    results: list[ExtractionResult],
    output_dir: Path,
) -> None:
    """
    Save extraction results to files.
    
    Args:
        pdf_path: Original PDF path
        results: List of extraction results
        output_dir: Directory to save results
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_name = pdf_path.stem
    
    # Save each extractor's output to a separate file
    for result in results:
        if result.success:
            output_file = output_dir / f"{pdf_name}_{result.extractor_name}.txt"
            output_file.write_text(result.text, encoding="utf-8")
    
    # Save comparison summary
    summary = {
        "pdf_file": str(pdf_path),
        "timestamp": datetime.now().isoformat(),
        "results": [
            {
                "extractor": r.extractor_name,
                "success": r.success,
                "error": r.error_message,
                "execution_time_seconds": r.execution_time_seconds,
                "char_count": r.char_count,
                "word_count": r.word_count,
                "line_count": r.line_count,
            }
            for r in results
        ],
    }
    
    summary_file = output_dir / f"{pdf_name}_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def generate_report(
    all_results: dict[str, list[ExtractionResult]],
    output_dir: Optional[Path] = None,
) -> str:
    """
    Generate a comprehensive comparison report.
    
    Args:
        all_results: Dict mapping PDF paths to their extraction results
        output_dir: Optional directory to save the report
        
    Returns:
        Report as markdown string
    """
    lines = [
        "# PDF Text Extraction Comparison Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"Total PDFs tested: {len(all_results)}",
        "",
    ]
    
    # Per-PDF results
    for pdf_path, results in all_results.items():
        lines.extend([
            f"## {Path(pdf_path).name}",
            "",
            generate_comparison_table(results),
            "",
        ])
    
    # Overall summary
    lines.extend([
        "## Overall Summary",
        "",
    ])
    
    # Aggregate statistics by extractor
    extractor_stats: dict[str, dict] = {}
    for results in all_results.values():
        for r in results:
            if r.extractor_name not in extractor_stats:
                extractor_stats[r.extractor_name] = {
                    "success_count": 0,
                    "total_count": 0,
                    "total_time": 0.0,
                    "total_words": 0,
                }
            
            stats = extractor_stats[r.extractor_name]
            stats["total_count"] += 1
            if r.success:
                stats["success_count"] += 1
                stats["total_time"] += r.execution_time_seconds
                stats["total_words"] += r.word_count
    
    lines.extend([
        "| Extractor | Success Rate | Avg Time (s) | Avg Words |",
        "|-----------|--------------|--------------|-----------|",
    ])
    
    for name, stats in extractor_stats.items():
        success_rate = stats["success_count"] / stats["total_count"] * 100
        avg_time = stats["total_time"] / max(stats["success_count"], 1)
        avg_words = stats["total_words"] / max(stats["success_count"], 1)
        lines.append(
            f"| {name} | {success_rate:.0f}% | {avg_time:.2f} | {avg_words:.0f} |"
        )
    
    lines.append("")
    
    report = "\n".join(lines)
    
    if output_dir:
        report_file = output_dir / "comparison_report.md"
        report_file.write_text(report, encoding="utf-8")
    
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Extract text from PDFs using appropriate extractor based on classification"
    )
    parser.add_argument(
        "input",
        type=Path,
        help="PDF file or directory containing PDFs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory to save results (default: output/)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    
    args = parser.parse_args()
    
    # Find PDF files
    if args.input.is_file():
        pdf_files = [args.input]
    elif args.input.is_dir():
        pdf_files = list(args.input.glob("*.pdf"))
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        sys.exit(1)
    
    if not pdf_files:
        print(f"Error: No PDF files found in {args.input}")
        sys.exit(1)
    
    verbose = not args.quiet
    
    if verbose:
        print(f"Found {len(pdf_files)} PDF file(s)")
        print(f"Output directory: {args.output_dir}")
        print()
    
    # Run extractions
    all_results: dict[str, list[ExtractionResult]] = {}
    
    for pdf_file in pdf_files:
        if verbose:
            print(f"Processing: {pdf_file.name}")
        
        results = run_extraction(pdf_file, verbose=verbose)
        all_results[str(pdf_file)] = results
        
        # Save individual results
        save_results(pdf_file, results, args.output_dir)
        
        if verbose:
            print()
    
    # Generate and print report
    report = generate_report(all_results, args.output_dir)
    
    if verbose:
        print("=" * 60)
        print(report)
        print("=" * 60)
        print(f"\nResults saved to: {args.output_dir}")


if __name__ == "__main__":
    main()

