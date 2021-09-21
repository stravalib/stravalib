docs: docs/*.rst docs/conf.py docs/Makefile stravalib/*.py  ## generate html docs
 # omit tests dir from build
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
#	$(MAKE) -C docs linkcheck
