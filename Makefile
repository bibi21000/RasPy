# Makefile for RasPy
#

# You can set these variables from the command line.
BUILDDIR      = _build
NOSE          = /usr/local/bin/nosetests
NOSEOPTS      = --verbosity=2
NOSECOVER     = --cover-package=raspy,raspyweb,raspyui --cover-min-percentage= --with-coverage --cover-inclusive --cover-tests --cover-html --cover-html-dir=docs/html/coverage --with-html --html-file=docs/html/nosetests/nosetests.html
PYLINT        = /usr/local/bin/pylint
PYLINTOPTS    = --max-line-length=130 --max-args=9 --extension-pkg-whitelist=zmq

.PHONY: help clean all develop install uninstall cleandoc docs tests devtests pylint git deps

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  develop    to install RasPy for developpers"
	@echo "  install    to install RasPy for users"
	@echo "  uninstall  to uninstall RasPy"
	@echo "  deps       to install all dependencies"
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
	-rm -rf build
	-rm -rf dist
	-rm -rf raspy.egg-info
	-rm -rf src/raspy.egg-info
	-rm -rf raspyweb.egg-info
	-rm -rf src-web/raspyweb.egg-info
	-rm -Rf /usr/local/lib/python2.7/dist-packages/raspy*

deps:
	apt-get update -y -qq
	apt-get install -y -qq build-essential python2.7-dev python2.7-minimal python2.7 git python-pip
	apt-get install -y -qq libcairo2-dev libpango1.0-dev libglib2.0-dev libxml2-dev librrd-dev
	apt-get install -y -qq vsftpd
	-apt-get install -y -qq rrdcached
	-chmod 777 /var/run/rrdcached.sock
	apt-get remove -y -qq python-zmq libzmq1 libzmq-dev pylint
	pip install setuptools
	pip install docutils


docs: cleandocs
	-mkdir -p docs/html/nosetests
	-mkdir -p docs/html/coverage
	-mkdir -p docs/html/pylint
	$(NOSE) $(NOSEOPTS) $(NOSECOVER) tests/
	-$(PYLINT) --output-format=html $(PYLINTOPTS) src/raspy src/scripts src-web/raspyweb src-web/scripts src-ui/raspyweb src-ui/scripts >docs/html/pylint/report.html
	cd docs && make docs
	cp docs/_build/text/README.txt README.md
	@echo
	@echo "Documentation finished."

install:
	python setup.py install
	python setup-web.py install
	#sudo python setup-ui.py install
	@echo
	@echo "Installation for users finished."

develop:
	python setup.py develop
	python setup-web.py develop
	#sudo python setup-ui.py develop
	@echo
	@echo "Installation for developpers finished."

tests:
	export NOSESKIP=False && $(NOSE) $(NOSEOPTS) tests/ --with-progressive; unset NOSESKIP
	@echo
	@echo "Tests for Raspberry pi finished."

devtests:
	-mkdir -p docs/html/nosetests
	-mkdir -p docs/html/coverage
	$(NOSE) $(NOSEOPTS) $(NOSECOVER) tests/
	@echo
	@echo "Tests for developpers finished."

git: clean docs
	git commit -m "Auto-commit for docs" README.md docs/
	git push
	@echo
	@echo "Commits pushed on github."

pylint:
	-mkdir -p docs/html/pylint
	$(PYLINT) $(PYLINTOPTS) src/raspy src/scripts src-web/raspyweb src-web/scripts src-ui/raspyweb src-ui/scripts
	@echo
	@echo "Pylint finished."

all: clean docs
