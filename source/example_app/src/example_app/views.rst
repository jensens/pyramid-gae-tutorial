Prepare
=======

::
    
    >>> from example_app import models
    
Root Page
=========

::
    >>> response = layer.webtest.get('/')
    >>> 'Root' in response
    True

    >>> 'Initial Root Node' in response
    True

Other pages
===========

We must not have a test node/page already::
  
    >>> models.read_node('test1')
    Traceback (most recent call last):
    ...
    KeyError: 'node with name test1 does not exists'

Create a node/page::

    >>> node = models.create_node('test1', 'Test One', 'This is a first test.')
    >>> node 
    TreeModel(key=Key('TreeModel', 'test1'), body=u'This is a first test.', title=u'Test One')

    >>> response = layer.webtest.get('/test1')
    >>> 'Test One' in response
    True

    >>> 'This is a first test.' in response
    True

    
Non existent pages
==================

A 404 is expected for non existent nodes/pages::

    >>> response = layer.webtest.get('/nonexistent', status='404', expect_errors=True)
    >>> response.status
    '404 Not Found'
    

Example for interlude
=====================

Start Interactive Console for development, comment before checkin::

    >>> #interact(locals())
