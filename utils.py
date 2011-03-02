from yaml import load


def set_trace():
    import pdb, sys
    debugger = pdb.Pdb(stdin=sys.__stdin__,
        stdout=sys.__stdout__)
    debugger.set_trace(sys._getframe().f_back)
 
_modsettings = {} 
    
def loadSettings(settings='settings.yaml'):
    
    x= _modsettings
    if not x:
        try:
            _modsettings.update(load(open(settings,'r').read()))
        except IOError:
            pass
        
    return _modsettings

settings = loadSettings()