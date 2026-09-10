# SP²Bench v1.01 – Modern Linux Build

This repository provides a modern Linux-compatible build of the **SP²Bench (SPARQL Performance Benchmark) v1.01 data generator**.

The original SP²Bench generator was developed as C++ source code and distributed with precompiled binaries for Linux and Windows. Due to its age, the original Linux binary and source code may present compatibility issues on contemporary 64-bit Linux systems and modern C++ toolchains.

This repository contains the original source code together with **minimal build compatibility modifications** required to compile and execute the generator on a modern 64-bit Linux system.

## About SP²Bench

SP²Bench is a performance benchmark for the SPARQL query language. It provides a synthetic RDF data generator designed to produce datasets based on characteristics of the DBLP bibliographic database.

The generated data can be used to evaluate SPARQL query engines and related systems.

The original SP²Bench project is available at:

https://dbis.informatik.uni-freiburg.de/index.php%3Fproject=SP2B%252Fdownload.php.html

This repository is based on **SP²Bench version 1.01**.

## Changes from the Original Version

The original SP²Bench v1.01 source code was developed for older C++ environments. When compiling it with a contemporary version of `g++` on a modern 64-bit Linux system, several compatibility issues were encountered.

The modifications made in this repository are strictly limited to compilation compatibility. **No changes were made to the data generation algorithms, benchmark logic, or generated RDF structure.**

### 1. Removal of the `-m32` Compilation Flag

The original `Makefile` compiled the generator using the `-m32` flag:

```makefile
g++ -Wall -m32 -O2
```

This forces the generation of a 32-bit executable.

On a modern 64-bit Linux system, compilation failed because the required 32-bit development headers and libraries were not installed. The compilation flag was therefore changed to:

```makefile
g++ -Wall -O2
```

This allows the generator to be compiled as a native 64-bit executable.

No changes to the generator's functionality result from this modification.

### 2. Explicit Inclusion of `<cstring>`

Several source files use functions from the C string library without explicitly including the corresponding standard C++ header.

Modern C++ compilers require these declarations to be explicitly included.

The following functions produced compilation errors:

* `strlen`
* `strcpy`
* `strncpy`

The following header was added to the affected source files:

```cpp
#include <cstring>
```

The affected files were:

* `namepoolfile.cpp`
* `namepoolmgr.cpp`
* `missingcites.cpp`

These changes only provide the required declarations to the compiler and do not modify the behaviour of the program.

### 3. Explicit Inclusion of `<cstdlib>`

The source file `volumemgr.cpp` uses the `abort()` function without explicitly including the appropriate standard header.

Modern C++ compilers require:

```cpp
#include <cstdlib>
```

This header was therefore added to:

* `volumemgr.cpp`

As with the other modifications, this change does not alter the generator's behaviour.

## Compiler Warnings

When compiled using a modern version of `g++`, the source code produces several warnings related primarily to const-correctness.

For example:

```text
ISO C++ forbids converting a string constant to 'char*'
```

These warnings originate from legacy code patterns where string literals are passed to functions expecting `char*`.

The warnings were intentionally left unchanged.

Correcting them would require more extensive modifications to function signatures and data structures throughout the original source code. Such modifications could potentially introduce unintended changes to the original implementation.

Since these warnings do not prevent compilation and are unrelated to the functionality of the data generator, no changes were made.

## Building

### Requirements

The generator requires:

* A Linux system
* `make`
* `g++`

On Debian or Ubuntu-based systems, these can be installed with:

```bash
sudo apt update
sudo apt install build-essential
```

### Compilation

Clone this repository

Compile the generator:

```bash
make
```

After successful compilation, the executable will be generated as:

```text
sp2b_gen
```

You can verify the architecture of the generated executable with:

```bash
file sp2b_gen
```

On a typical 64-bit Linux system, the output should indicate a 64-bit ELF executable.

## Usage

The generator uses the following syntax:

```text
./sp2b_gen [BREAK_CONDITION] [OUTFILE]
```

### Generate the Default Dataset

Running the generator without arguments produces the default dataset:

```bash
./sp2b_gen
```

By default, the generator creates approximately 50,000 RDF triples.

The default output file is:

```text
sp2b.n3
```

### Generate a Specific Number of Triples

Use the `-t` option:

```bash
./sp2b_gen -t 1000000 sp2b_1M.nt
```

This generates approximately 1,000,000 RDF triples and writes them to:

```text
sp2b_1M.nt
```

### Generate a Dataset by Size

The `-s` option specifies the desired output size in kilobytes:

```bash
./sp2b_gen -s 10000 sp2b_10MB.nt
```

## Output Format

The generated datasets use a simple RDF serialization compatible with N-Triples-style RDF data.

The generated data can be imported into RDF stores and SPARQL systems such as GraphDB.

For example, the generated data can be loaded into a GraphDB repository and queried through its SPARQL endpoint.

## Reproducibility

The modifications in this repository are intentionally minimal.

The following changes were made:

1. The `-m32` compilation flag was removed to allow native compilation on 64-bit Linux systems.
2. `#include <cstring>` was added where required for C string functions.
3. `#include <cstdlib>` was added where required for `abort()`.

No changes were made to:

* The RDF data generation algorithms.
* The statistical distributions used by the generator.
* The generated RDF vocabulary.
* The structure of generated RDF triples.
* The command-line interface.
* The benchmark methodology.

Therefore, these modifications are intended solely to make the original SP²Bench v1.01 generator compatible with contemporary Linux systems and C++ compilers.

## Original SP²Bench License

The SP²Bench data generator was originally published under the Berkeley License.

Please refer to the original `COPYING` file included with the SP²Bench distribution for the complete licensing information.

## Citation

If you use SP²Bench in academic work, please cite the original SP²Bench publication.

This repository provides a compatibility build of SP²Bench v1.01 and does not introduce a new benchmark or modification to the benchmark methodology.

## Disclaimer

This repository is not an official distribution of SP²Bench.

It contains the original SP²Bench v1.01 source code together with minimal modifications required for successful compilation on contemporary 64-bit Linux systems using modern C++ toolchains.
