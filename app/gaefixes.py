# fix sys path to include dists
import sys
import os
sys.path.insert(0, 'distlib')

# register gae loader for pkg_resources
if os.environ.get('SERVER_SOFTWARE', 'Development')[0:11] == "Development":
    from google.appengine.tools.dev_appserver_import_hook import \
        HardenedModulesHook
    from pkg_resources import register_loader_type, DefaultProvider
    register_loader_type(HardenedModulesHook, DefaultProvider)

# disable chameleon debug module loader, gae does not allow tempdirs
import chameleon.template
from chameleon.loader import MemoryLoader
chameleon.template._make_module_loader = MemoryLoader
chameleon.template.BaseTemplate.loader = MemoryLoader()
