.PHONY: all docs microraiden

DOCS_SRC := docs
DOCS_BUILD := build/docs

all: docs microraiden

docs:
	sphinx-build -b html $(DOCS_SRC) $(DOCS_BUILD)

microraiden:
	make -C microraiden

clean:
	make -C microraiden clean
	rm -rf $(DOCS_BUILD)
