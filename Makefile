VERSION=$(shell python setup.py --version)
FULLNAME=$(shell python setup.py --fullname)

PACKAGES=$(patsubst debian/%.install,dist/%_$(VERSION)_all.deb,$(wildcard debian/*.install))
SRCFILES=$(shell find silk | grep .py$$)

TESTPYTHON=PYTHONPATH=$(PWD)/build/lib.linux-$(shell uname -p)-2.7 python
DOCTEST=$(TESTPYTHON) -m doctest

all: build
.PHONY: all clean test sdist deb install-deb docs BLANK debian/install

BLANK:

clean:
	@debuild clean
	@python setup.py clean

test: build
	@$(TESTPYTHON) doctest/rundoctests.py
	@$(TESTPYTHON) doctest/testwebdbdrivers.py
	@$(TESTPYTHON) -m doctest doctest/*.txt

build: $(SRCFILES)
	@python setup.py build

debian/python-silk-common.install: BLANK
	ls silk | grep \\.py$$ | awk '{ print "debian/tmp/usr/lib/python*/*-packages/" $$0}' > $@

debian/python-silk-webdb.install: BLANK
	ls -d silk/webdb/* silk/webdb/drivers/* | egrep '/(__init__|base|sqlite)\.py$$' | awk '{ print "debian/tmp/usr/lib/python*/*-packages/" $$0}' > $@

debian/python-silk-webdb-mysql.install: BLANK
	echo "debian/tmp/usr/lib/python*/*-packages/silk/webdb/drivers/mysql.py" > $@

debian/python-silk-webdoc.install: BLANK
	find silk/webdoc | grep \\.py$$ | awk '{ print "debian/tmp/usr/lib/python*/*-packages/" $$0}' > $@

debian/python-silk-webreq.install: BLANK
	find silk/webreq | grep \\.py$$ | awk '{ print "debian/tmp/usr/lib/python*/*-packages/" $$0}' > $@

debian/install: debian/python-silk-common.install debian/python-silk-webdb.install debian/python-silk-webdb-mysql.install debian/python-silk-webdoc.install debian/python-silk-webreq.install 

dist/%.deb: debian/%.install

deb: $(FULLNAME).tar.gz debian/install
	@cd dist; $(UNSUDO) tar -xf $(FULLNAME).tar.gz; cd $(FULLNAME) ; debuild -i -uc -us
	@echo "Packages can be found under dist/"

sdist: $(FULLNAME).tar.gz

$(FULLNAME).tar.gz:
	@python setup.py sdist

$(PACKAGES): deb

install-deb: $(PACKAGES)
	@dpkg -i $(PACKAGES)

docs: $(patsubst %.txt,%.html,$(wildcard doctest/*.txt))

doctest/%.html: doctest/%.txt
	@$(DOCTEST) $^ && rst2html $^ $@
