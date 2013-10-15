Prepare
=======

::
    
    >>> from example_app import models    

Create
------

creating a first node::

    >>> node = models.create_node('test1', 'Test One', 'This is a first test.')
    >>> node 
    TreeModel(key=Key('TreeModel', 'test1'), body=u'This is a first test.', title=u'Test One')

creating a second node::

    >>> node = models.create_node('test2', 'Test Two', 'This is a 2nd test.')
    >>> node 
    TreeModel(key=Key('TreeModel', 'test2'), body=u'This is a 2nd test.', title=u'Test Two')

trying to create a node that already exists raises ValueError::

    >>> node = models.create_node('test1', 'Test One', 'This is a first test.')
    Traceback (most recent call last):
    ...
    ValueError: node with name test1 already exists

    
Read
----

reading non existent node raises keyerror::
  
    >>> models.read_node('nonexistent')
    Traceback (most recent call last):
    ...
    KeyError: 'node with name nonexistent does not exists'


readin existent node returns it::

    >>> models.read_node('test1')
    TreeModel(key=Key('TreeModel', 'test1'), body=u'This is a first test.', title=u'Test One')

    
Get Root
--------

ROOT node does not exist::

    >>> models.read_node('ROOT')
    Traceback (most recent call last):
    ...
    KeyError: 'node with name ROOT does not exists'

Create root on first access::

    >>> models.get_root({})
    TreeModel(key=Key('TreeModel', 'ROOT'), body=u'Initial Root Node', title=u'Root')    
    
    >>> models.read_node('ROOT')
    TreeModel(key=Key('TreeModel', 'ROOT'), body=u'Initial Root Node', title=u'Root')    

Subsequent call are working too::

    >>> models.get_root({})
    TreeModel(key=Key('TreeModel', 'ROOT'), body=u'Initial Root Node', title=u'Root')    
    