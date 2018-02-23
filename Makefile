.PHONY: all docs microraiden apidocs clean mrproper

DOCS_SRC := docs
BUILD_DIR := build
DOCS_BUILD_DIR := $(BUILD_DIR)/docs
DATADIR:=microraiden/data

all: docs webui flake8

pip-install:
	pip install .

pip-install-dev:
	pip install -e . -r requirements-dev.txt

docs: pydocs jsdocs

pydocs: apidocs
	sphinx-build -b html $(DOCS_SRC) $(DOCS_BUILD_DIR)

apidocs:
	sphinx-apidoc -o $(DOCS_SRC)/api microraiden/

jsdocs:
	cd microraiden/webui/microraiden/ && npm run docs

clean:
	python setup.py clean --all
	rm -vrf $(BUILD_DIR) ./dist ./*.pyc ./*.tgz ./*.egg-info

mrproper: clean

bandit:
	bandit -s B101 -r microraiden/

pylint:
	pylint microraiden/

ssl_cert:
	openssl req -x509 -newkey rsa:4096 -nodes -out $(DATADIR)/cert.pem -keyout $(DATADIR)/key.pem -days 365

flake8:
	flake8 microraiden/

webui:
	python setup.py compile_webui

