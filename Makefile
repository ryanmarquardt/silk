VERSION=$(shell python setup.py --version)
FULLNAME=$(shell python setup.py --fullname)
PACKAGES=python-silk_$(VERSION)_all.deb python-silk-common_$(VERSION)_all.deb python-silk-webdoc_$(VERSION)_all.deb python-silk-webdb_$(VERSION)_all.deb python-silk-webdb-mysql_$(VERSION)_all.deb python-silk-webreq_$(VERSION)_all.deb

TESTPYTHON=PYTHONPATH=$(PWD)/build/lib.linux-$(shell uname -p)-2.7 python
DOCTEST=$(TESTPYTHON) -m doctest

all: deb
.PHONY: all clean test public sdist deb install current build

clean:
	@debuild clean
	@python setup.py clean

test: build
	$(TESTPYTHON) doctest/rundoctests.py
	$(TESTPYTHON) -m doctest doctest/*.txt

public: clean
	@if test -n "`git status --porcelain`" ; then git status; exit 1; else git push; fi

current:
	@git pull

build:
	@python setup.py build

sdist:
	@if python setup.py sdist ; then cd dist; tar -xf $(FULLNAME).tar.gz; fi

deb: sdist
	@cd dist/$(FULLNAME) ; debuild -i -uc -us

install-deb:
	@cd dist ; dpkg -i $(PACKAGES)
