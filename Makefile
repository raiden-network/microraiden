.PHONY: all docs microraiden apidocs clean mrproper

DOCS_SRC := docs
BUILD_DIR := build
DOCS_BUILD_DIR := $(BUILD_DIR)/docs

all: docs microraiden

docs: apidocs
	sphinx-build -b html $(DOCS_SRC) $(DOCS_BUILD_DIR)

apidocs:
	sphinx-apidoc -o $(DOCS_SRC)/api microraiden/microraiden/

microraiden:
	make -C microraiden

clean:
	make -C microraiden clean
	rm -rf $(BUILD_DIR)

mrproper: clean
