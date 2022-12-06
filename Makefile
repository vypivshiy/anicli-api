# Treat these arguments not as files, but as recipes
.PHONY: venv venv-prod githooks check fix

# Used to execute all in one shell
.ONESHELL:

# Default recipe
DEFAULT: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Use poetry or activated venv
interpreter := $(shell poetry env info --path > /dev/null 2>&1 && echo "poetry run")


check-venv:
	$(if $(interpreter),, $(error No poetry environment found, either run "make venv"))

venv: ## Create virtual environment and install ALL dependencies
	@python3 -m pip install poetry
	@poetry install && \
	echo; echo "Poetry created virtual environment and installed all dependencies"

venv-prod: ## Create virtual environment and install ONLY prod dependencies
	@python3 -m pip install poetry
	@poetry install --without dev && \
	echo; echo "Poetry created virtual environment and installed only prod dependencies"

githooks: check-venv  ## Install git hooks
	@$(interpreter) pre-commit install -t=pre-commit -t=pre-push

check: check-venv ## Run tests and linters
	@echo "flake8"
	@echo "------"
	@$(interpreter) flake8 .
	@echo ; echo "black"
	@echo "-----"
	@$(interpreter) black --check .
	@echo ; echo "isort"
	@echo "----"
	@$(interpreter) isort --check-only .
	@echo ; echo "mypy"
	@echo "----"
	@$(interpreter) mypy .
	@echo ; echo "pytest"
	@echo "------"
	@$(interpreter) pytest

fix: check-venv ## Fix code with black and isort
	@echo "black"
	@echo "-----"
	@$(interpreter) black .
	@echo ; echo "isort"
	@echo "-----"
	@$(interpreter) isort .

gen-docs: check-venv
	@echo "Generate documentation"
	@echo "----------------------"
	@sphinx-apidoc -f -o docs anicli_api/ anicli_api/extractors/* anicli_api/decoders/*
	@echo "generate html"
	@echo "-------------"
	@make -C docs clean html
