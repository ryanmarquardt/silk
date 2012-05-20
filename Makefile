test:
	@PYTHONPATH=$(PWD) python webdoc/__init__.py
	@PYTHONPATH=$(PWD) python webdb/__init__.py
	@PYTHONPATH=$(PWD) python -m doctest doctest/*.txt
