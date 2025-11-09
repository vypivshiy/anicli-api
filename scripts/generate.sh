#!/usr/bin/env sh

ssc-gen py dev/player -i lxml -s "_parser.py" -o "anicli_api/player/parsers"
ssc-gen py dev/src -i lxml -s "_parser.py" -o "anicli_api/source/parsers"
