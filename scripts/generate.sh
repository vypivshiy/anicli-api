repo_dir="libanime_schema"
github_repo="https://github.com/libanime/libanime_schema"

# TODO check updates
if [ -d "$repo_dir" ]; then
    echo "Directory $repo_dir already exists."
else
    echo "Directory $repo_dir does not exist. Cloning the repository..."
    git clone "$github_repo" "$repo_dir"
fi

ssc-gen libanime_schema/source/animego.yaml python.parsel -o anicli_api/source/parsers/animego_parser.py -y
ssc-gen libanime_schema/source/animania.yaml python.parsel -o anicli_api/source/parsers/animania_parser.py -y
ssc-gen libanime_schema/source/animejoy.yaml python.parsel -o anicli_api/source/parsers/animejoy_parser.py -y
ssc-gen libanime_schema/source/sovetromantica.yaml python.parsel -o anicli_api/source/parsers/sovetromantica_parser.py -y
