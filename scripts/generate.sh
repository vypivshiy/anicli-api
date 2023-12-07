#!/bin/bash

repo_dir="libanime_schema"
github_repo="https://github.com/libanime/libanime_schema"

clone_repository() {
    echo "Cloning the repository..."
    git clone "$github_repo" "$repo_dir"
}

check_and_clone_repository() {
    if [ -d "$repo_dir" ]; then
        echo "Directory $repo_dir already exists, generate"
    else
        clone_repository
    fi
}

generate_parser() {
    ssc-gen "$1" "$2" -o "$3" -y
}

# Check and clone the repository
check_and_clone_repository

# Generate parsers
generate_parser "libanime_schema/source/animego.yaml" "python.parsel" "anicli_api/source/parsers/animego_parser.py"
generate_parser "libanime_schema/source/animania.yaml" "python.parsel" "anicli_api/source/parsers/animania_parser.py"
generate_parser "libanime_schema/source/animejoy.yaml" "python.parsel" "anicli_api/source/parsers/animejoy_parser.py"
generate_parser "libanime_schema/source/sovetromantica.yaml" "python.parsel" "anicli_api/source/parsers/sovetromantica_parser.py"
