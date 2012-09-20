============================================================
Pyramid on Google’s App Engine (the easy way using buildout)
============================================================

A minimal Pyramid application running in a local appengine development
environment.

The `zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ based installation
is based on the `great appengine buildout integration appfy.recipe.gae <http://pypi.python.org/pypi/appfy.recipe.gae/>`_.

This minimal example was a based on `some older pyramid on appengine
tutorial <http://code.google.com/p/bfg-pages/wiki/PyramidTutorial>` and
developed further since I had some issues to get it running I cleaned it
slightly up, such as moving the app to the app subdir and now it just works.

Usage
=====

Follow the white rabbit::

    git clone git://github.com/jensens/pyramid-gae-tutorial.git
    cd pyramid-gae-tutorial
    /path/to/python2.7 bootstrap.py
    ./bin/buildout
    ./bin/dev_appserver app

And in your browser just point to ``http://localhost:8080``.

Additional information
======================

``pgk_resources``
    ``./app/pkg_resources.py`` was copied from `distribute <http://packages.python.org/distribute/>`_
    and you may want to keep it uptodate. To make it work  I had to register the
    appengine loader to ``pkg_resources.DefaultProvider`` in ``./app/main.py``.

Source Code
===========

The sources are in a GIT DVCS with its main branches at
`github <http://github.com/jensens/pyramid-gae-tutorial>`_.

I'd be happy to see many forks and pull-requests to make it even better.

Contributors
============

- Jens W. Klein <jk@kleinundpartner.at>
