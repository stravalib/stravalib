# Makefile for Sphinx documentation

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXAUTOGEN = sphinx-autogen
BUILDDIR      = _build

# User-friendly check for sphinx-build
ifeq ($(shell which $(SPHINXBUILD) >/dev/null 2>&1; echo $$?), 1)
$(error The '$(SPHINXBUILD)' command was not found. Make sure you have Sphinx installed, then set the SPHINXBUILD environment variable to point to the full path of the '$(SPHINXBUILD)' executable. Alternatively you can add the directory with the executable to your PATH. If you don't have Sphinx installed, grab it from http://sphinx-doc.org/)
endif

# Internal variables.
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees  $(SPHINXOPTS) .

.PHONY: help clean html

# This runs if you run make -C docs from the root dir
# This has to go above help to work by default
all: html

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  all        generate the complete documentation api and regular"
	@echo "  html       make only the HTML files from the existing rst sources"
	@echo "  clean      clean all local doc directories out"
	@echo "  serve      serve the docs locally using sphinx autobuild"
	
# Run: make -C docs clean 
clean:
	rm -rf $(BUILDDIR)/html/*
	rm -rf $(BUILDDIR)/doctrees
	rm -rf .ipynb_checkpoints

html: 
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

## Serve live docs in a browser
serve:
	pwd
	sphinx-autobuild ../docs _build/html
