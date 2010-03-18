#!/usr/bin/env cxpython
import sys
from lib import options, cmapi
from lib.cmapitags import *

def log(s):
    sys.stdout.flush()
    sys.stderr.write(s)
    sys.stderr.flush()

sess = cmapi.Session()
stores = [sess.store(row[PR_ENTRYID])
          for row in sess.stores().iter(PR_ENTRYID)]

optspec = """
crampi [options] [folders...]
--
F,folders   list subfolders of the given folders
L,list      list the messages in the given folders
"""
o = options.Options('crampi', optspec)
(opt, flags, extra) = o.parse(sys.argv[1:])

if not (opt.folders or opt.list):
    o.fatal('must provide -F or -L')

if opt.folders:
    def show_cont(indent, c):
        for eid,name,subf in c.children().iter(PR_ENTRYID, PR_DISPLAY_NAME_W,
                                               PR_SUBFOLDERS):
            print '%s%s' % (indent, name)
            if subf:
                show_cont(indent+'    ', c.child(eid))
    if not extra:
        show_cont('', sess)
    else:
        for name in extra:
            show_cont('', sess.recursive_find(name))

if opt.list:
    if not extra:
        o.fatal('must provide a folder name to list')
    for name in extra:
        f = sess.recursive_find(name)
        for m in f.messages().iter(PR_NORMALIZED_SUBJECT, PR_TITLE_W):
            print repr(m.get(PR_NORMALIZED_SUBJECT+1000, m))
