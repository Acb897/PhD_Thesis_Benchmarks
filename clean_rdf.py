#!/usr/bin/env python3
"""
RDF Cleaner - Sanitize and repair common syntax issues in RDF files.

This script processes N-Triples (.nt), Turtle (.ttl), and Notation3 (.n3) files
in a given directory tree. It performs two main automatic repairs:

1. Percent-escapes selected illegal or problematic characters inside IRIs (<...>)
2. Merges multiline statements into single-line triples

Files are first validated using the `rapper` command-line tool (from librdf/raptor).
Valid files are copied unchanged; invalid files are cleaned and saved to a
parallel directory structure under `rdf_cleaned/`.

Each processed file receives a `.changelog.json` documenting what (if anything)
was modified.

Usage:
    python3 clean_rdf.py /path/to/dataset

Output structure:
    dataset/
    ├── data.nt
    └── rdf_cleaned/
        ├── data.nt
        └── data.nt.changelog.json

Requirements:
    - Python 3.6+
    - Optional but strongly recommended: `rapper` (librdf/raptor utils)

License: MIT
"""

import os
import sys
import re
import json
import subprocess
import shutil
import time
from datetime import datetime
from typing import Dict, Any, Tuple, List

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS = (".nt", ".ttl", ".n3")
"""File extensions this tool will process (case-insensitive)."""

CLEAN_FOLDER_NAME = "rdf_cleaned"
"""Name of the output subdirectory where cleaned files are written."""

ILLEGAL_IRI_CHARS: Dict[str, str] = {
    " ": "%20",
    '"': "%22",
    "<": "%3C",
    ">": "%3E",
    "{": "%7B",
    "}": "%7D",
    "|": "%7C",
    "^": "%5E",
    "`": "%60",
}
"""Mapping of characters that should be percent-escaped inside IRIs."""

IRI_PATTERN = re.compile(r"<([^>]*)>")
"""Regular expression to match IRI content between angle brackets."""


# ──────────────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────────────

def log(message: str, level: str = "INFO") -> None:
    """
    Print a timestamped log message to stdout.

    Args:
        message: The message to log.
        level: Log level (INFO, WARNING, ERROR). Used only for display.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


# ──────────────────────────────────────────────────────────────────────────────
# IRI Sanitization
# ──────────────────────────────────────────────────────────────────────────────

def sanitize_iri(iri: str) -> Tuple[str, bool]:
    """
    Replace illegal/problematic characters in an IRI with percent-encoding.

    Args:
        iri: The raw IRI string (content inside <...>)

    Returns:
        Tuple of (cleaned IRI, whether any change was made)
    """
    modified = False
    parts: List[str] = []
    for char in iri:
        if char in ILLEGAL_IRI_CHARS:
            parts.append(ILLEGAL_IRI_CHARS[char])
            modified = True
        else:
            parts.append(char)
    return "".join(parts), modified


def fix_iri(line: str, changes: Dict[str, Any], line_number: int) -> str:
    """
    Replace problematic IRIs in a line and record changes.

    Args:
        line: A single RDF statement line (or merged multiline statement)
        changes: Dictionary tracking modifications (modified in-place)
        line_number: Original line number for changelog

    Returns:
        The line with sanitized IRIs
    """
    def replacer(match: re.Match) -> str:
        original = match.group(1)
        cleaned, was_modified = sanitize_iri(original)
        if was_modified:
            changes["iri_sanitized"]["count"] += 1
            changes["iri_sanitized"]["details"].append({
                "line": line_number,
                "before": original,
                "after": cleaned
            })
        return f"<{cleaned}>"

    return IRI_PATTERN.sub(replacer, line)


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

def validate_with_rapper(file_path: str, timeout: int = 300) -> bool:
    """
    Check whether an RDF file is syntactically valid using the rapper tool.

    Args:
        file_path: Path to the RDF file
        timeout: Maximum time (seconds) to wait for rapper

    Returns:
        True if rapper reports the file as valid, False otherwise
        (also returns False if rapper is missing or times out)
    """
    try:
        result = subprocess.run(
            ["rapper", "-i", "guess", "-c", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode == 0:
            log(f"Rapper validation successful: {file_path}")
            return True
        else:
            log(f"Rapper validation FAILED: {file_path}", "WARNING")
            log(f"Rapper stderr: {result.stderr.strip()}", "WARNING")
            return False

    except FileNotFoundError:
        log("rapper not found. Install librdf/raptor to enable validation.", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        log(f"rapper timed out after {timeout}s: {file_path}", "WARNING")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# File Processing
# ──────────────────────────────────────────────────────────────────────────────

def process_file(input_file: str, dataset_root: str) -> None:
    """
    Process a single RDF file: validate → clean if needed → save result.

    Args:
        input_file: Absolute path to the input RDF file
        dataset_root: Root directory of the dataset (used for relative paths)
    """
    log(f"Processing file: {input_file}")

    relative_path = os.path.relpath(input_file, dataset_root)
    clean_root = os.path.join(dataset_root, CLEAN_FOLDER_NAME)
    output_file = os.path.join(clean_root, relative_path)
    changelog_file = output_file + ".changelog.json"

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Step 1: Try quick validation
    if validate_with_rapper(input_file):
        log(f"File is valid → copying unchanged: {relative_path}")
        shutil.copy2(input_file, output_file)
        # Empty changelog
        changes = {
            "iri_sanitized": {"count": 0, "details": []},
            "multiline_merged": {"count": 0, "details": []},
        }
        with open(changelog_file, "w", encoding="utf-8") as f:
            json.dump(changes, f, indent=4)
        return

    # Step 2: Cleaning required
    log(f"Validation failed → starting cleaning: {relative_path}")

    # Count total lines for progress reporting
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        total_lines = sum(1 for _ in f)

    changes: Dict[str, Any] = {
        "iri_sanitized": {"count": 0, "details": []},
        "multiline_merged": {"count": 0, "details": []},
    }

    buffer = ""
    processed_lines = 0
    start_time = time.time()
    next_progress = 0.1

    with open(input_file, "r", encoding="utf-8", errors="ignore") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line_number, line in enumerate(infile, start=1):
            processed_lines += 1
            stripped = line.rstrip("\n")

            # Merge multiline statements
            if not stripped.strip().endswith("."):
                buffer += stripped + " "
                continue

            full_line = buffer + stripped
            buffer = ""

            if full_line != stripped:
                changes["multiline_merged"]["count"] += 1
                changes["multiline_merged"]["details"].append({
                    "line": line_number,
                    "merged_triple": full_line.strip()
                })

            # Sanitize IRIs
            fixed_line = fix_iri(full_line, changes, line_number)
            outfile.write(fixed_line + "\n")

            # Progress reporting
            progress = processed_lines / total_lines
            if progress >= next_progress:
                log(f"{processed_lines}/{total_lines} lines processed "
                    f"({int(next_progress * 100)}%)")
                next_progress += 0.1

        if buffer:
            log("Warning: unbalanced/multiline structure at end of file", "ERROR")

    # Save changelog
    with open(changelog_file, "w", encoding="utf-8") as f:
        json.dump(changes, f, indent=4)

    elapsed = time.time() - start_time
    log(f"Finished cleaning: {output_file} in {elapsed:.2f}s")
    log(f"Changelog written: {changelog_file}")

    # Optional: validate cleaned version
    validate_with_rapper(output_file)


# ──────────────────────────────────────────────────────────────────────────────
# Directory Traversal
# ──────────────────────────────────────────────────────────────────────────────

def traverse_dataset(dataset_root: str) -> None:
    """
    Recursively find and process all supported RDF files in the dataset.

    Skips the output directory (`rdf_cleaned`) to prevent re-processing.

    Args:
        dataset_root: Root path of the dataset directory
    """
    for root, dirs, files in os.walk(dataset_root):
        if CLEAN_FOLDER_NAME in root.split(os.sep):
            continue

        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)
                process_file(full_path, dataset_root)


# ──────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Command-line entry point."""
    if len(sys.argv) != 2:
        print("Usage: python3 clean_rdf.py <dataset_path>")
        sys.exit(1)

    dataset_path = sys.argv[1]

    if not os.path.isdir(dataset_path):
        print("Error: dataset_path must be a directory.")
        sys.exit(1)

    log(f"Starting RDF cleaning for dataset: {dataset_path}")
    traverse_dataset(dataset_path)
    log("All files processed.")


if __name__ == "__main__":
    main()
