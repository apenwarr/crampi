from lib import options, cmapi
from lib.cmapitags import *
from lib.helpers import *

optspec = """
crampi mapi-folders <folder names...>
"""

def show_cont(prefix, c):
    for eid,name,has_subfolders in c.subfolders():
        print '%s%s' % (prefix, name)
        if has_subfolders:
            try:
                show_cont(prefix+name+'/', c.child(eid,name))
            except cmapi.OpenFailed, e:
                log('error: %r\n' % e)


def main(argv):
    o = options.Options('crampi mapi-folders', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    sess = cmapi.Session()
    if not extra:
        show_cont('', sess)
    else:
        for name in extra:
            show_cont(name+'/', sess.recursive_find(name))
