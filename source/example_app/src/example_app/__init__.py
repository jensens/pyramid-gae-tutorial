from .models import get_root

def includeme(config):
    config.set_root_factory(get_root)
    config.scan('.views')
