import logging

logging.getLogger().setLevel(logging.INFO)

import sys, os

sys.path.insert(0, 'lib/dist')

# register gae loader
from google.appengine.tools.dev_appserver_import_hook import HardenedModulesHook
from pkg_resources import register_loader_type, DefaultProvider
register_loader_type(HardenedModulesHook, DefaultProvider)

from pyramid.config import Configurator
from models import get_root

settings = {
    'reload_templates': 'false',
    'debug_authorization': 'false',
    'debug_notfound': 'false',
    'debug_templates': 'false',
    'default_locale_name': 'en',
}


config = Configurator(root_factory=get_root, settings=settings)
config.add_view('views.my_view',
                context='models.MyModel',
                renderer='templates/mytemplate.pt')
application = config.make_wsgi_app()
