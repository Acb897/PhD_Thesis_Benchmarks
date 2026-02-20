# RDF Cleaner – Sanitize and Repair N-Triples / Turtle / N3 Files

**rdf-cleaner** is a lightweight, practical Python tool that automatically repairs common syntax issues in RDF files (mainly N-Triples `.nt`, Turtle `.ttl`, and N3 `.n3`) so they can be parsed by strict RDF libraries and triple stores (Jena, RDFlib, rapper/raptor, Blazegraph, GraphDB, etc.).

It performs two targeted fixes:

- Percent-escapes illegal or problematic characters inside IRIs (`<…>`)
- Merges multiline statements into single-line triples (very common in broken crawler dumps)

## Features

- Safe percent-encoding of dangerous IRI characters  
  (`space → %20`, `" → %22`, `< → %3C`, `> → %3E`, `{ → %7B`, `} → %7D`, `| → %7C`, `^ → %5E`, `` ` → %60``)
- Automatic merging of multiline triples / blank node lists / collections
- Uses `rapper` (Raptor parser) to validate files before and after cleaning
- Skips already-valid files (fast copy only)
- Detailed per-file change logs in JSON format
- Progress reporting & timestamped console logging
- UTF-8 tolerant reading (ignores encoding errors)
- Preserves directory structure in output folder `rdf_cleaned/`

## Requirements

- Python 3.6+
- `librdf` / `raptor` command-line tool (`rapper`) – **strongly recommended**

  **Ubuntu/Debian**
  ```bash
  sudo apt update
  sudo apt install librdf0-utils
  ```

  **macOS (Homebrew)**
  ```bash
  brew install raptor
  ```

> If `rapper` is not available, the script still runs but skips validation steps and always attempts cleaning.

## Installation

```bash
# Clone the repository (recommended)
git clone https://github.com/yourusername/rdf-cleaner.git
cd rdf-cleaner

# Or just download the single file clean_rdf.py
```

No `pip install` required — it's a standalone script.

## Usage

Basic command:

```bash
python3 clean_rdf.py /path/to/your/rdf/dataset
```

Real-world examples:

```bash
# Current directory dataset
python3 clean_rdf.py .

# Specific folder
python3 clean_rdf.py ./broken_rdf_dump/

# Large crawl collection
python3 clean_rdf.py /data/crawled-rdf/2025-crawl/
```

What happens:

1. Creates a folder `rdf_cleaned/` inside the given directory
2. Validates every `.nt`, `.ttl`, `.n3` file using `rapper`
3. Copies valid files unchanged
4. Cleans invalid files → saves results to `rdf_cleaned/...`
5. Writes a `filename.changelog.json` next to each processed file

## Output Structure

```
your_dataset/
├── file1.nt
├── dirA/
│   └── broken.ttl
└── rdf_cleaned/                # ← created automatically
    ├── file1.nt
    ├── file1.nt.changelog.json
    └── dirA/
        └── broken.ttl
            └── broken.ttl.changelog.json
```

### Example changelog file (`file.nt.changelog.json`)

```json
{
  "iri_sanitized": {
    "count": 14,
    "details": [
      {
        "line": 23,
        "before": "http://example.org/bad space in/iri",
        "after": "http://example.org/bad%20space%20in/iri"
      },
      ...
    ]
  },
  "multiline_merged": {
    "count": 5,
    "details": [
      {
        "line": 187,
        "merged_triple": "<http://ex.org/s> <http://ex.org/p> <http://ex.org/o1> , <http://ex.org/o2> ."
      }
    ]
  }
}
```

## Supported File Formats

| Extension | Format       | Notes                          |
|-----------|--------------|--------------------------------|
| `.nt`     | N-Triples    | Primary target                 |
| `.ttl`    | Turtle       | Supported, best-effort         |
| `.n3`     | Notation3    | Supported, best-effort         |

## Limitations & Known Issues

- Only escapes a predefined small set of problematic characters (can be extended)
- Multiline merging relies on statements ending with `.` — very malformed files may still fail
- Does **not** fix:
  - Incorrect literal escaping
  - Missing/wrong prefix declarations
  - Malformed datatypes or language tags
  - Unicode normalization issues
- Validation depends on `rapper`

## License

[MIT License](LICENSE)

Feel free to use, modify, and distribute.
