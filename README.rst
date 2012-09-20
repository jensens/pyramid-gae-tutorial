============================================================
Pyramid on Google’s App Engine (the easy way using buildout)
============================================================

Usage
=====

This was a based on one older offical pyramid tutorial and developed further
since I had some issues to get it running I cleaned it slightly up, such as
moving the app to the app subdir and now it just works with a clean
Python 2.7 using::
	
    /path/to/python2.7 bootstrap.py
    ./bin/buildout
    ./bin/dev_appserver app

And in your browser just point to ``http://localhost:8080``.

Additional information
======================

``pgk_resources``
    ``./app/pkg_resources.py`` was copied from `distribute <http://packages.python.org/distribute/>`_
    and you may want to keep it uptodate. To make it work in ``./app/main.py``
    I had to register the appengine loader to ``pkg_resources.DefaultProvider``.

Source Code
===========

The sources are in a GIT DVCS with its main branches at
`github <http://github.com/jensens/pyramid-gae-tutorial>`_.

I'd be happy to see many forks and pull-requests to make it even better.

Contributors
============

- Jens W. Klein <jk@kleinundpartner.at>
