all: sdist

clean:
	@python setup.py clean

test:
	@PYTHONPATH=$(PWD) python webdoc/__init__.py
	@PYTHONPATH=$(PWD) python webdb/__init__.py
	@PYTHONPATH=$(PWD) python -m doctest doctest/*.txt

public:
	@if test -n "`git status --porcelain`" ; then git status; exit 1; else git push; fi

sdist:
	@python setup.py sdist
