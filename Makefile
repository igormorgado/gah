REQUIREMENTS := base torch ml
PYTHON_VERSION := 3.11
NEO4J_VERSION := 5.23.0
VENV := gah-env

.DEFAULT_GOAL := start

.PHONY: install dev clean docker pyvenv langs start help uninstall purge $(REQUIREMENTS)

install: $(REQUIREMENTS)
	pip install -U $(foreach req,$(REQUIREMENTS), -r requirements-$(req).txt)

dev: install
	pip install -U -r requirements-dev.txt
	@echo pip install -e .

$(REQUIREMENTS): 
	pip install -U -r requirements-$@.txt

clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@rm -rf build dist
	@echo "Cleanup complete."

docker:
	@docker run -d \
	  --publish=7474:7474 \
	  --publish=7687:7687 \
	  --user="$(id -u):$(id -g)" \
	  --env NEO4J_apoc_export_file_enabled=true \
	  --env NEO4J_apoc_import_file_enabled=true \
	  --env NEO4J_apoc_import_file_use__neo4j__config=true \
	  --env NEO4J_PLUGINS='["graph-data-science", "apoc"]' \
	  --name neo4j \
	  neo4j:$(NEO4J_VERSION)

pyvenv:
	@echo "Installing Python version $(PYTHON_VERSION)"
	pyenv install $(PYTHON_VERSION)
	@echo "Creating the virtual env '$(VENV)'"
	pyenv virtualenv $(PYTHON_VERSION) $(VENV)
	@echo "Setting as local '$(VENV)'"
	pyenv local $(VENV)
	@echo Reopen your shell to activate the virtual env then execute:
	@echo
	@echo "    make install"
	@echo


langs:
	@python -m spacy download en_core_web_trf
	@python -m spacy download en_core_web_lg
	@python -m spacy download en_core_web_md
	@python -m spacy download en_core_web_sm
	@python -m spacy download pt_core_news_lg
	@python -m spacy download pt_core_news_md
	@python -m spacy download pt_core_news_sm
	@python -m coreferee install en
	# @pip install https://github.com/explosion/spacy-experimental/releases/download/v0.6.1/en_coreference_web_trf-3.4.0a2-py3-none-any.whl

start:
	@echo Starting Docker NEO4J image.
	docker start neo4j
	@echo Starting Jupyter Lab
	jupyter lab --no-browser &

uninstall:
	@echo Removing language packages
	pip uninstall -y en-core-web-lg en-core-web-md en-core-web-sm en-core-web-trf \
               		 pt-core-news-lg pt-core-news-md pt-core-news-sm 
	#	               en-coreference-web-trf 
	@echo Uninstall python package

purge:
	@echo Remove docker images
	@echo Remove virtualenv

# Help target
help:
	@echo "Available targets:"
	@echo "  help      - Show this help message."
	@echo "  install   - Install all requirements."
	@echo "  dev       - Install dev packages and make it editable."
	@echo "  clean     - Clean caches."
	@echo "  docker    - Install neo4j docker images."
	@echo "  pyvenv    - Make pyenv virtualenv. Requires pyenv virtualenv."
	@echo "  langs     - Install SpaCy language packages."
	@echo "  start     - Initiate the environment. Everything must be installed."
	@echo "  uninstall - To remove the python package"
	@echo "  purge     - To remove venv and docker images"
