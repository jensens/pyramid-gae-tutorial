import gaefixes
import logging
from yaml import load

logging.getLogger().setLevel(logging.INFO)

from pyramid.config import Configurator

config = Configurator(settings=load(open('settings.yaml','r').read()))
# config.hook_zca()
config.add_route('root', '/')
config.scan('views')
application = config.make_wsgi_app()
