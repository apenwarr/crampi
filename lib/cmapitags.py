from win32com.mapi import mapi
from win32com.mapi.mapitags import *

class PropertyError(Exception):
    pass

def _get_id(handle, name):
    ps = '{00062004-0000-0000-C000-000000000046}'  # magic Outlook GUID
    pt = handle.GetIDsFromNames([(ps,name)], 0)[0]
    if pt == PT_ERROR:
        raise PropertyError("Can't find property named %r" % name)
    return PROP_TAG(PT_UNICODE, PROP_ID(pt))

def pr_custom(name):
    def lookup(h):
        return _get_id(h, name)
    return lookup
