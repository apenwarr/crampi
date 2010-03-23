from lib import options, cmapi
from lib.cmapitags import *

optspec = """
crampi mapi-folders <folder names...>
"""

def show_cont(indent, c):
    for eid,name,subf in c.children().iter(PR_ENTRYID, PR_DISPLAY_NAME_W,
                                           PR_SUBFOLDERS):
        print '%s%s' % (indent, name)
        if subf:
            show_cont(indent+'    ', c.child(eid))


def main(argv):
    o = options.Options('crampi mapi-folders', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    sess = cmapi.Session()
    if not extra:
        show_cont('', sess)
    else:
        for name in extra:
            show_cont('', sess.recursive_find(name))
