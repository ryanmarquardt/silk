VERSION=$(shell python setup.py --version)
FULLNAME=$(shell python setup.py --fullname)

PACKAGES=$(patsubst debian/%.install,dist/%_$(VERSION)_all.deb,$(wildcard debian/*.install))
SRCFILES=$(shell find silk | grep .py$$)

TESTPYTHON=PYTHONPATH=$(PWD)/build/lib.linux-$(shell uname -p)-2.7 python
DOCTEST=$(TESTPYTHON) -m doctest

all: build
.PHONY: all clean test sdist deb install-deb docs

clean:
	@debuild clean
	@python setup.py clean

test: build
	@$(TESTPYTHON) doctest/rundoctests.py
	@$(TESTPYTHON) doctest/testwebdbdrivers.py
	@$(TESTPYTHON) -m doctest doctest/*.txt

build: $(SRCFILES)
	@python setup.py build

deb: $(PACKAGES)
	@echo "Packages can be found under dist/"

sdist: $(FULLNAME).tar.gz

$(FULLNAME).tar.gz:
	@python setup.py sdist

$(PACKAGES): $(FULLNAME).tar.gz
	@cd dist; $(UNSUDO) tar -xf $(FULLNAME).tar.gz; cd $(FULLNAME) ; debuild -i -uc -us

install-deb: $(PACKAGES)
	dpkg -i $(PACKAGES)

docs: $(patsubst %.txt,%.html,$(wildcard doctest/*.txt))

doctest/%.html: doctest/%.txt
	$(DOCTEST) $^ && rst2html $^ $@
