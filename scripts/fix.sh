#!/bin/sh -e

export PREFIX=""
if [ -d '.venv' ] ; then
    export PREFIX=".venv/bin/"
fi
export SOURCE_FILES="anicli_api"

set -x
