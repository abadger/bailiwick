#!/bin/sh
set -e
poetry run python -m pytest \
	--cov-branch --cov=bailiwick --cov-report term-missing \
	-vv tests "$@"
