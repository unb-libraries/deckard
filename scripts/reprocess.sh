#!/usr/bin/env bash
# rm -rf data/collectors/libpages/cache/*
rm -rf data/chunkers/standard/output/*
poetry run build:rag libpages
poetry run api
