import logging

logging.getLogger().setLevel(logging.INFO)

import sys,os

sys.path.insert(0,'lib/dist')

from pyramid.configuration import Configurator
from models import get_root
from google.appengine.ext.webapp.util import run_wsgi_app

settings = {
    'reload_templates': 'false',
    'debug_authorization': 'false',
    'debug_notfound': 'false',
    'debug_templates': 'false',
    'default_locale_name': 'en',
}

def main():
    """ This function runs a Pyramid WSGI application.
    """
    
    config = Configurator(root_factory=get_root,settings=settings)
    config.add_view('views.my_view',
                    context='models.MyModel',
                    renderer='templates/mytemplate.pt')
    app= config.make_wsgi_app()
    run_wsgi_app(app)
            
if __name__ == '__main__':
  main() 