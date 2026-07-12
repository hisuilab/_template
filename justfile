set shell := ["bash", "-euo", "pipefail", "-c"]

# requires: treefmt
format:
    treefmt

# requires: treefmt
check-format:
    treefmt --fail-on-change

# requires: git, prek
precommit:
    ./scripts/precommit

# requires: rumdl
check-docs:
    if [ -d docs ]; then rumdl check --config rumdl.toml docs/; fi

# requires: git
check-readme:
    ./scripts/check-readme

# requires: git
check-status:
    ./scripts/check-status

# requires: git
check-encoding:
    ./scripts/check-encoding

# requires: bats
test-bats:
    bats --recursive tests/unit

# requires: pytest
test-py:
    pytest

# requires: bats, pytest
test: test-bats test-py

lint: check-format

verify: test lint check-docs check-readme check-status check-encoding
