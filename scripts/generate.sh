#!/usr/bin/env sh
ssc-gen generate -t py-lxml -o "anicli_api/player/parsers" dev/player
ssc-gen generate -t py-lxml -o "anicli_api/source/parsers" dev/src
