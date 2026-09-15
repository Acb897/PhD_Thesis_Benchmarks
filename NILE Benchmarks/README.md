# NILE Benchmark Profiling Notebook

This directory contains the notebook `Benchmarks.ipynb`, which benchmarks the generation of structural profiles for multiple RDF datasets by running SPHINX against each dataset's SPARQL endpoint.

## Purpose

The notebook measures:

- how long each dataset takes to extract patterns from the endpoint
- how long SPHINX takes to generate a SHACL profile from those patterns
- how many node shapes and property shapes are present in the generated profile
- how large the resulting profile is on disk
- how large the profile is relative to the dataset size

This makes it possible to compare benchmark datasets under a consistent methodology and to record the results in CSV files for further analysis.

## What the notebook does

The workflow is structured in five stages:

1. Record the execution environment
2. Profile one endpoint as a smoke test
3. Profile every configured endpoint repeatedly in a measured loop
4. Aggregate the repetitions and count dataset size
5. Export the summary table and save the per-run measurements

## Requirements

Before running the measured loop, ensure that:

- the `nile` package is installed and importable
- every endpoint listed in the notebook is running and reachable
- the output folders are writable

The notebook expects the dataset endpoints to be available at the configured URLs, and it is designed to continue even if one endpoint fails so that the rest of the measurements are retained.

## Configuration

The notebook defines:

- `OUTPUT_DIR`: temporary working directory used during repeated profiling runs
- `PROFILE_DIR`: directory where one profile per dataset is kept
- `REPEATS`: number of times each dataset is profiled
- `DISCARD_FIRST`: whether to ignore the first repetition as a warm-up
- `VERBOSE`: whether to display SPHINX progress output
- `endpoints`: a mapping from dataset labels to SPARQL endpoint URLs

The endpoints are written as explicit labels rather than derived from the URL to avoid ambiguous names for services such as QLever.

## Outputs

When the notebook is run, it writes the following files to the working directory:

- `profile_runs.csv`: raw per-run benchmark measurements
- `profile_benchmarks.csv`: aggregated summary table across repeated runs

The notebook also stores one generated profile per dataset in `PROFILE_DIR`.

## Methodology

For each dataset and each repetition:

- a fresh SPHINX engine is constructed
- the output directory is cleared before the run to avoid duplicate files
- the generated profile is copied into `PROFILE_DIR` under the dataset label
- timing is recorded for both extraction and SHACL generation
- the first repetition may be discarded as warm-up when `DISCARD_FIRST = True`

The notebook reports both the mean and median of the total runtime, and it also checks whether repeated runs produced identical profiles.

## Notes

- Timing is wall-clock time rather than CPU time because the work is dominated by network requests to the endpoints.
- A failed dataset is recorded in the output with its error status instead of stopping the whole benchmark process.
- Dataset sizes are measured after the profiling loop by querying the endpoint with `SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }`.

## Related files

- `Benchmarks.ipynb`: the notebook containing the benchmarking workflow
- `../README.md`: project-level overview of the repository
