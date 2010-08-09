from lib import options, gitdb, entry

optspec = """
crampi validate [refname]
--
d,gitdb=   name of gitdb sqlite3 database file [crampi.sqlite3]
"""

def main(argv):
    o = options.Options('crampi validate', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if extra:
        o.fatal('no arguments expected')

    g = gitdb.GitDb(opt.gitdb)
    for r,ref,msg in reversed(list(g.commits(refname=None))):
        print '%-6d %-10s %s' % (r,ref,msg)
        entry.load_tree_from_commit(g, r)
        
