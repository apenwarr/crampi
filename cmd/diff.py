from lib import options, gitdb, entry

optspec = """
crampi diff <commitid|refname> <commitid|refname>
--
d,gitdb=   name of gitdb sqlite3 database file [gitdb.sqlite3]
s,short    only show changed uuids, not changes to contents
"""

def main(argv):
    o = options.Options('crampi diff', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 2:
        o.fatal('exactly two arguments expected; use "crampi log" for a list')

    g = gitdb.GitDb(opt.gitdb)

    def lookup(s):
        if g.commit(s):
            return s
        else:
            c = g.commitid_latest(s)
            if not c:
                o.fatal('%r: not found; specify a valid refname or commitid'
                        % s)
            return c
    c1 = lookup(extra[0])
    c2 = lookup(extra[1])

    entries1 = entry.load_tree_from_commit(g, c1)
    entries2 = entry.load_tree_from_commit(g, c2)

    def printrow(key, old, new):
        if key:
            key = '%s: ' % key
        else:
            key = ''
        if old != None and old == new:
            print ' %s%s' % (key, old)
        else:
            if old != None:
                print '-%s%s' % (key, old)
            if new != None:
                print '+%s%s' % (key, new)

    for uuid,ad,bd in entry.diff(entries1, entries2):
        if not ad: ad = {}
        if not bd: bd = {}
        if ad == bd:
            continue
        printrow(None, ad and uuid or None, bd and uuid or None)
        if not opt.short:
            for key in sorted(set(ad.keys()) | set(bd.keys())):
                printrow(key, ad.get(key), bd.get(key))
            print
