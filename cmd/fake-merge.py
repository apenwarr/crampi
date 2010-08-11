import datetime, time
from lib import options, gitdb, merge, entry

optspec = """
crampi fake-merge
--
d,gitdb=   name of gitdb sqlite3 database file [crampi.sqlite3]
b,branch=  name of git branch to merge into
m,merge=   name of git branch to (pretend to) merge from
v,verbose  print names as they are exported
"""

def main(argv):
    o = options.Options('crampi fake-merge', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra):
       o.fatal('no arguments expected')
    if not opt.branch:
        o.fatal('you must specify the -b option')
    if not opt.merge:
        o.fatal('you must specify the -m option')

    g = gitdb.GitDb(opt.gitdb)
    
    cid = g.commitid_latest(opt.branch)
    if not cid:
        o.fatal('nonexistent commit: %r' % opt.branch)

    el = entry.load_tree_from_commit(g, cid)
    print merge.run(g, el, opt.branch, opt.merge, opt.verbose,
                    add_contact = lambda d: None,
                    update_contact = lambda lid, d, changes: None,
                    commit_contacts = lambda: None,
                    reload_entrylist = lambda el: el)
    g.flush()
