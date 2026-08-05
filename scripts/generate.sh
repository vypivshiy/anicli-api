#!/usr/bin/env sh
# ssc-gen generate -R -t py-lxml -o "anicli_api/player/parsers" --http-client httpx dev/player
# ssc-gen generate -R -t py-lxml -o "anicli_api/source/parsers" --http-client httpx dev/src 
ssc-gen generate python .\dev\player -L lxml -R -o .\anicli_api\player\parsers
ssc-gen generate python .\dev\src -L lxml -R -o .\anicli_api\source\parsers
