from lib import options, cmapi
from lib.cmapitags import *

optspec = """
crampi mapi-list <folder names...>
"""

def main(argv):
    o = options.Options('crampi mapi-list', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if not extra:
       o.fatal('you must provide at least one folder name')

    sess = cmapi.Session()
    for name in extra:
        f = sess.recursive_find(name)
        for m in f.messages().iter(PR_NORMALIZED_SUBJECT, PR_TITLE_W):
            print repr(m.get(PR_NORMALIZED_SUBJECT+1000, m))

