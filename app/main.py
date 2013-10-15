import gaefixes  # first

from appglobals import APP_BASE_DIR, DEBUG
import logging
import os
from pyramid.config import Configurator
from yaml import load

if DEBUG():
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)

SETTINGS_FILE = os.path.join(APP_BASE_DIR, 'settings.yaml')


def app_config():
    config = Configurator(settings=load(open(SETTINGS_FILE, 'r').read()))
    config.add_settings({'currentapp.basedir': APP_BASE_DIR})
    config.add_translation_dirs('example_app:locale/')
    config.hook_zca()
    config.include('example_app')
    # config.add_route('catchall', '{notfound:.*}')
    return config

config = app_config()
application = config.make_wsgi_app()
