Pyramid on Google’s App Engine (the easy way using buildout)
============================================================

A example Pyramid application running in a local appengine development
environment.

The `zc.buildout <http://pypi.python.org/pypi/zc.buildout>`_ based installation
uses the `appengine buildout integration collective.recipe.appengine <https://github.com/jensens/collective.recipe.appengine>`_.

This example was a based on
`some older pyramid on appengine tutorial <http://code.google.com/p/bfg-pages/wiki/PyramidTutorial>`_
and was developed further, because I had some issues to get it running. I
cleaned it slightly up, such as moving the app to the app subdir and now it
just works.

Usage
-----

Preconditions:

- virtual-env >= 1.9

Follow the white rabbit::

    git clone git://github.com/jensens/pyramid-gae-tutorial.git
    cd pyramid-gae-tutorial
    /path/to/virtualenv-2.7 --no-setuptools --no-site-packages --clear .
    ./bin/python2.7 bootstrap.py
    ./bin/buildout

Run tests::

    ./bin/testpy -m example_app

Run apps local development server::

    ./bin/dev_appserver 


And in your browser just point to ``http://localhost:8080``. For
admin-interface go to ``http://localhost:9000``.


Additional information
----------------------

``pgk_resources``
    ``./app/pkg_resources.py`` was copied from `distribute <http://packages.python.org/distribute/>`_
    and you may want to keep it uptodate. To make it work  I had to register the
    appengine loader to ``pkg_resources.DefaultProvider`` in ``./app/main.py``.

TODO:
-----

- Check if ``pkg_resources`` is still needed after reunion of setuptools and distribute.

- Check how we can work with pycrypto and Pillow in a sane way in this environment.

Source Code
-----------

The sources are in a GIT DVCS with its main branches at
`github <http://github.com/jensens/pyramid-gae-tutorial>`_.

I'd be happy to see many forks and pull-requests to make it even better.

Contributors
------------

- Jens W. Klein <jk@kleinundpartner.at>
