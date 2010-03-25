import sqlite3, yaml
from lib import options, gitdb, entry, ffcrm

optspec = """
crampi crm-export [options] crmdb.sqlite3
--
d,gitdb=   name of gitdb sqlite3 database file
b,branch=  name of git branch to use for these files
v,verbose  print names as they are exported
"""

def main(argv):
    o = options.Options('crampi crm-export', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
        o.fatal('exactly one argument expected')
    opt.crmdb = extra[0]

    if not opt.gitdb:
        opt.gitdb = 'gitdb.sqlite3'
    if not opt.branch:
        opt.branch = 'crm-default'

    g = gitdb.GitDb(opt.gitdb)
    s = sqlite3.connect(opt.crmdb)
    el = entry.Entries(ffcrm.entries(s))
    el.uuids_from_commit(g, opt.branch)
    el.assign_missing_uuids(g)
    if opt.verbose:
        for e in sorted(el.entries, key = lambda x: x.uuid):
            print e
    print el.save_commit(g, opt.branch)
    g.flush()
 
