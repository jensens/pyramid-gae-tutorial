from google.appengine.ext import ndb
import logging


class TreeModel(ndb.Model):
    title = ndb.StringProperty()
    body = ndb.TextProperty()

    def __getitem__(self, name):
        return read_node(name)


def create_node(name, title, body):
    try:
        read_node(name)
    except KeyError, e:
        node = TreeModel(id=name, title=title, body=body)
        node.put()
        return node
    raise ValueError('node with name %s already exists' % name)


def read_node(name):
    node = ndb.Key(TreeModel, name).get()
    if not node:
        raise KeyError('node with name %s does not exists' % name)
    return node


def get_root(request):
    try:
        root = read_node('ROOT')
        logging.info('root found: %s' % root)
    except KeyError:
        root = create_node('ROOT', 'Root', 'Initial Root Node')
        logging.info('root created: %s' % root)
    return root

