#!/usr/bin/env bash

ssc-gen py libanime_schema/player -i parsel -s "_parser.py" -o "anicli_api/player/parsers"

ssc-gen py libanime_schema/src -i parsel -s "_parser.py" -o "anicli_api/source/parsers"
