VERSION=$(shell python setup.py --version)
PACKAGES=../python-silk_$(VERSION)_all.deb ../python-silk-common_$(VERSION)_all.deb ../python-silk-webdoc_$(VERSION)_all.deb ../python-silk-webdb_$(VERSION)_all.deb ../python-silk-webdb-all_$(VERSION)_all.deb

all: deb
.PHONY: all clean test public sdist deb install current

clean:
	@debuild clean

test: clean
	@PYTHONPATH=$(PWD) python silk/__init__.py
	@PYTHONPATH=$(PWD) python silk/webdoc/__init__.py
	@PYTHONPATH=$(PWD) python silk/webdb/__init__.py
	@PYTHONPATH=$(PWD) python -m doctest doctest/*.txt

public: clean
	@if test -n "`git status --porcelain`" ; then git status; exit 1; else git push; fi

current:
	@git pull

sdist:
	@python setup.py sdist

deb:
	@debuild -i -uc -us

install:
	@dpkg -i $(PACKAGES)
