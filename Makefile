VERSION=$(shell python setup.py --version)
PACKAGES=../python-webdoc_$(VERSION)_all.deb ../python-webdb_$(VERSION)_all.deb

all: deb
.PHONY: all clean test public sdist deb install current

clean:
	@rm -r build
	@debuild clean

test:
	@PYTHONPATH=$(PWD) python webdoc/__init__.py
	@PYTHONPATH=$(PWD) python webdb/__init__.py
	@PYTHONPATH=$(PWD) python -m doctest doctest/*.txt

public:
	@if test -n "`git status --porcelain`" ; then git status; exit 1; else git push; fi

current:
	@git pull

sdist:
	@python setup.py sdist

deb: test
	@debuild -b -i -uc -us

install:
	@dpkg -i $(PACKAGES)
