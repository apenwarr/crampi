from lib import options, gitdb, entry

optspec = """
crampi dump <commitid|refname>
--
d,gitdb=   name of gitdb sqlite3 database file [crampi.sqlite3]
"""

def main(argv):
    o = options.Options('crampi dump', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
        o.fatal('exactly one argument expected; use "crampi log" for a list')
        
    g = gitdb.GitDb(opt.gitdb)
    if g.commit(extra[0]):
        commitid = extra[0]
    else:
        commitid = g.commitid_latest(extra[0])
        if not commitid:
            o.fatal('invalid argument; specify a valid refname or commitid')

    entries = entry.load_tree_from_commit(g, commitid)

    for e in entries.entries:
        for k,v in sorted(e.d.items()):
            print '%s: %r' % (k,v)
        print
