# autocards

<div align="center">

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/YYYasin/autocards/blob/master/.pre-commit-config.yaml)
![Coverage Report](assets/images/coverage.svg)

Automatically generate flashcards from text files and PDFs using LLMs.

</div>

## Installation

Install using `pixi`:

```bash
pixi install
pixi run postinstall
```

## Usage

The CLI is very bare-bones right now. It only supports generating flashcards from a single file.

```bash
autocards --help
Usage: autocards [OPTIONS] [DECK_NAME] [SOURCE_PATH] [OUTPUT_PATH]

Options:
  --page-range TEXT
  --num-questions INTEGER
  --help                   Show this message and exit.
```

An example command for the `example/example.pdf` would be

```bash
autocards my-deck example/example.pdf example.apkg --page-range '1-10' --num-questions 20
```

This creates a file called `deck_name.apkg` in the current directory.
