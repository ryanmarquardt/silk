VERSION=$(shell python setup.py --version)
FULLNAME=$(shell python setup.py --fullname)
PACKAGES=python-silk_$(VERSION)_all.deb python-silk-common_$(VERSION)_all.deb python-silk-webdoc_$(VERSION)_all.deb python-silk-webdb_$(VERSION)_all.deb python-silk-webdb-mysql_$(VERSION)_all.deb python-silk-webreq_$(VERSION)_all.deb

TESTPYTHON=PYTHONPATH=$(PWD)/build/lib.linux-$(shell uname -p)-2.7 python
DOCTEST=$(TESTPYTHON) -m doctest

all: build
.PHONY: all clean test public sdist deb install current build

clean:
	@debuild clean
	@python setup.py clean

test: build
	@$(TESTPYTHON) doctest/rundoctests.py
	@$(TESTPYTHON) doctest/testwebdbdrivers.py
	@$(TESTPYTHON) -m doctest doctest/*.txt

build:
	@python setup.py build

deb:
	@if python setup.py sdist ; then cd dist; tar -xf $(FULLNAME).tar.gz; cd $(FULLNAME) ; debuild -i -uc -us; fi
	@echo "Packages can be found under dist/"

install-deb: deb
	@cd dist ; dpkg -i $(PACKAGES)
