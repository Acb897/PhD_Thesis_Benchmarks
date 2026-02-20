#!/usr/bin/env python3
import os
import sys
import re
import json
import subprocess
import shutil
import time
from datetime import datetime

# ------------------------------
# Configuration
# ------------------------------
SUPPORTED_EXTENSIONS = (".nt", ".ttl", ".n3")
CLEAN_FOLDER_NAME = "rdf_cleaned"
ILLEGAL_IRI_CHARS = {
    " ": "%20",
    '"': "%22",
    "<": "%3C",
    ">": "%3E",
    "{": "%7B",
    "}": "%7D",
    "|": "%7C",
    "^": "%5E",
    "`": "%60"
}
iri_pattern = re.compile(r"<([^>]*)>")

# ------------------------------
# Logging with timestamps
# ------------------------------
def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

# ------------------------------
# IRI sanitization
# ------------------------------
def sanitize_iri(iri):
    modified = False
    new_iri = []
    for c in iri:
        if c in ILLEGAL_IRI_CHARS:
            new_iri.append(ILLEGAL_IRI_CHARS[c])
            modified = True
        else:
            new_iri.append(c)
    return "".join(new_iri), modified

def fix_iri(line, changes, line_number):
    def replacer(match):
        original = match.group(1)
        cleaned, modified = sanitize_iri(original)
        if modified:
            changes["iri_sanitized"]["count"] += 1
            changes["iri_sanitized"]["details"].append({
                "line": line_number,
                "before": original,
                "after": cleaned
            })
        return f"<{cleaned}>"
    return iri_pattern.sub(replacer, line)

# ------------------------------
# Rapper validation with timeout
# ------------------------------
def validate_with_rapper(file_path, timeout=300):
    """
    Validate RDF file with rapper.
    Returns True if valid, False if invalid, timed out, or rapper not found.
    """
    try:
        result = subprocess.run(
            ["rapper", "-i", "guess", "-c", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            log(f"Rapper validation successful: {file_path}")
            return True
        else:
            log(f"Rapper validation FAILED: {file_path}", "WARNING")
            log(f"Rapper stderr: {result.stderr.strip()}", "WARNING")
            return False
    except FileNotFoundError:
        log("Rapper not found. Please install librdf/raptor.", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        log(f"Rapper timed out after {timeout}s: {file_path}", "WARNING")
        return False

# ------------------------------
# File processing (cleaning)
# ------------------------------
def process_file(input_file, dataset_root):
    log(f"Processing file: {input_file}")
    relative_path = os.path.relpath(input_file, dataset_root)
    clean_root = os.path.join(dataset_root, CLEAN_FOLDER_NAME)
    output_file = os.path.join(clean_root, relative_path)
    changelog_file = output_file + ".changelog.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # First attempt: validate with rapper
    if validate_with_rapper(input_file):
        log(f"File is valid, copying to cleaned folder: {relative_path}")
        shutil.copy2(input_file, output_file)
        # Write empty changelog
        changes = {"iri_sanitized": {"count": 0, "details": []},
                   "multiline_merged": {"count": 0, "details": []}}
        with open(changelog_file, "w", encoding="utf-8") as log_file:
            json.dump(changes, log_file, indent=4)
        return

    # If invalid or rapper failed → start cleaning
    log(f"Validation failed. Starting cleaning for {relative_path}")

    # Count total lines for progress reporting
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        total_lines = sum(1 for _ in f)

    changes = {
        "iri_sanitized": {"count": 0, "details": []},
        "multiline_merged": {"count": 0, "details": []}
    }

    buffer = ""
    processed_lines = 0
    start_time = time.time()
    next_progress = 0.1  # next 10% threshold

    with open(input_file, "r", encoding="utf-8", errors="ignore") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:

        for line_number, line in enumerate(infile, start=1):
            processed_lines += 1
            stripped = line.rstrip("\n")

            # Merge multiline triples
            if not stripped.strip().endswith("."):
                buffer += stripped + " "
                continue
            else:
                full_line = buffer + stripped
                buffer = ""
                if full_line != stripped:
                    changes["multiline_merged"]["count"] += 1
                    changes["multiline_merged"]["details"].append({
                        "line": line_number,
                        "merged_triple": full_line
                    })

                # Fix IRIs
                fixed_line = fix_iri(full_line, changes, line_number)
                outfile.write(fixed_line + "\n")

            # Progress reporting at 10% intervals
            if processed_lines / total_lines >= next_progress:
                log(f"{processed_lines}/{total_lines} lines processed "
                    f"({int(next_progress*100)}%)")
                next_progress += 0.1

        if buffer:
            log("Unbalanced structure at end of file", "ERROR")

    # Write changelog
    with open(changelog_file, "w", encoding="utf-8") as log_file:
        json.dump(changes, log_file, indent=4)

    elapsed = time.time() - start_time
    log(f"Finished cleaning: {output_file} in {elapsed:.2f}s")
    log(f"Changelog written: {changelog_file}")

    # Validate cleaned file
    validate_with_rapper(output_file)

# ------------------------------
# Dataset traversal
# ------------------------------
def traverse_dataset(dataset_root):
    for root, dirs, files in os.walk(dataset_root):
        # Skip rdf_cleaned folder
        if CLEAN_FOLDER_NAME in root.split(os.sep):
            continue
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                full_path = os.path.join(root, file)
                process_file(full_path, dataset_root)

# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
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