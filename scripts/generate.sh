#!/usr/bin/env bash

ssc-gen \
libanime_schema/player -c py.parsel --suffix "_parser" -o 'anicli_api/player/parsers'

ssc-gen \
libanime_schema/src -c py.parsel --suffix "_parser" -o 'anicli_api/source/parsers'
