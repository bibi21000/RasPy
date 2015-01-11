# Makefile for RasPy
#

# You can set these variables from the command line.
BUILDDIR      = _build
NOSE          = /usr/local/bin/nosetests
NOSEOPTS      = --verbosity=2
NOSECOVER     = --cover-package=raspy --cover-min-percentage= --with-coverage --cover-inclusive --cover-tests --cover-html --cover-html-dir=docs/html/coverage --with-html --html-file=docs/html/nosetests/nosetests.html
PYLINT        = /usr/local/bin/pylint
PYLINTOPTS    = --max-line-length=130 --max-args=9 --extension-pkg-whitelist=zmq

.PHONY: help clean all develop install uninstall cleandoc docs tests devtests pylint git

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  develop    to install RasPy for developpers"
	@echo "  install    to install RasPy for users"
	@echo "  uninstall  to uninstall RasPy"
	@echo "  docs       to make all documentation"
	@echo "  tests      to launch tests for users"
	@echo "  devtests   to launch detailled tests for developpers"
	@echo "  pylint     to check code quality"
	@echo "  git        to publish RasPy on GitHub"
	@echo "  clean      to clean the development directory"
	@echo "  cleandocs  to clean the documentation generated"

cleandocs: clean
	-rm -rf docs/html
	-rm -rf docs/pdf

clean:
	-rm -rf $(BUILDDIR)
	-rm -rf .raspy_test
	-rm -rf .raspy_test2
	-find . -name *.pyc -delete
	cd docs && make clean

uninstall: clean
	-sudo rm -rf build
	-sudo rm -rf dist
	-sudo rm -rf raspy.egg-info
	-sudo rm -rf src/raspy.egg-info
	-sudo rm -Rf /usr/local/lib/python2.7/dist-packages/raspy*

docs: cleandocs
	-mkdir -p docs/html/nosetests
	-mkdir -p docs/html/coverage
	-mkdir -p docs/html/pylint
	-$(NOSE) $(NOSEOPTS) $(NOSECOVER) tests/
	-$(PYLINT) --output-format=html $(PYLINTOPTS) src/raspy src/scripts >docs/html/pylint/report.html
	cd docs && make docs
	cp docs/_build/text/README.txt README.md
	@echo
	@echo "Documentation finished."

install:
	sudo python setup.py install
	@echo
	@echo "Installation for users finished."

develop:
	sudo python setup.py develop
	@echo
	@echo "Installation for developpers finished."

tests:
	export NOSESKIP=False && $(NOSE) $(NOSEOPTS) tests/ --with-progressive; unset NOSESKIP
	@echo
	@echo "Tests for Raspberry pi finished."

devtests:
	-mkdir -p docs/html/nosetests
	-mkdir -p docs/html/coverage
	-$(NOSE) $(NOSEOPTS) $(NOSECOVER) tests/
	@echo
	@echo "Tests for developpers finished."

git: clean docs
	git commit -m "Auto-commit for docs" README.md docs/
	git push
	@echo
	@echo "Commits pushed on github."

pylint:
	-mkdir -p docs/html/pylint
	-$(PYLINT) $(PYLINTOPTS) src/raspy src/scripts
	@echo
	@echo "Pylint finished."

all: clean devtests pylint docs
