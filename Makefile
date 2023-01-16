TESTDIR=tmp-test-dir-stravalib
PYTEST_ARGS=--cov stravalib stravalib/tests/unit stravalib/tests/integration

help:
	@echo "Commands:"
	@echo ""
	@echo "  install   install package in editable mode"
	@echo "  test      run the test suite (including doctests) and report coverage"
	@echo "  build     build source and wheel distributions"
	@echo "  clean     clean up build and generated files"
	@echo ""


build:
	python -m build

install:
	python -m pip install --no-deps -e .

test:
	# Create tmp dir to ensure that tests are run on the installed version of stravalib
	mkdir -p $(TESTDIR)
	cd $(TESTDIR);
	python -m pytest $(PYTEST_ARGS) $(PROJECT)
	rm -r $(TESTDIR)

## Clean up all unneeded files and directories and things that shouldn't be under version control
clean:
	find . -name "*.pyc" -exec rm -v {} \;
	find . -name "*.orig" -exec rm -v {} \;
	find . -name ".coverage.*" -exec rm -v {} \;
	rm -rvf build dist MANIFEST *.egg-info __pycache__ .coverage .cache .pytest_cache $(PROJECT)/_version_generated.py
