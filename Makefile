docs: docs/*.rst docs/conf.py docs/Makefile stravalib/*.py  ## generate html docs
	# -fMeET -o docs/api stravalib stravalib/tests/ stravalib/tests/unit stravalib/tests/functional # omit tests dir from build
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(MAKE) -C docs linkcheck
