import sqlite3, time
from lib import options, gitdb, entry, ffcrm

optspec = """
crampi ffcrm [options] crmdb.sqlite3
--
d,gitdb=   name of gitdb sqlite3 database file [gitdb.sqlite3]
b,branch=  name of git branch to use for CRM data
m,merge=   name of git branch to merge from
v,verbose  print names as they are exported
"""

def main(argv):
    o = options.Options('crampi ffcrm', optspec)
    (opt, flags, extra) = o.parse(argv[1:])

    if len(extra) != 1:
        o.fatal('exactly one argument expected')
    opt.crmdb = extra[0]

    if not opt.branch:
        o.fatal('you must specify the -b option')

    g = gitdb.GitDb(opt.gitdb)
    s = sqlite3.connect(opt.crmdb)
    el = entry.Entries(ffcrm.entries(s))
    el.uuids_from_commit(g, opt.branch)
    el.assign_missing_uuids(g)
    if opt.verbose:
        for e in sorted(el.entries, key = lambda x: x.uuid):
            print e
    print el.save_commit(g, opt.branch, 'exported from ffcrm %r' % opt.crmdb)

    if opt.merge:
        a_id = g.commitid_lastmerge(refname=opt.branch,
                                    merged_refname=opt.merge)
        b_id = g.commitid_latest(opt.merge)
        print 'aid=%s bid=%s' % (a_id, b_id)
        a = entry.load_tree_from_commit(g, a_id)
        b = entry.load_tree_from_commit(g, b_id)
        nel = el.clone()
        for (lid,uuid,ed,ad,bd) in entry.merge(el, a, b):
            d = None
            if not ed: # add
                mode = 'A'
                assert(bd)
                lid = ffcrm.add_contact(s, bd)
                e = entry.Entry(lid, uuid, bd)
                el.entries.append(e)
            elif ad and not bd:  # del
                mode = 'D'
                e = el.uuids[uuid]
            elif ad != bd: # modify
                mode = 'M'
                e = el.uuids[uuid]
                e.patch(ad, bd)
                ffcrm.update_contact(s, lid, e.d)
            else:
                mode = ''
                e = el.uuids[uuid]
            if mode or opt.verbose:
                print '%1s %s' % (mode, e)
        s.commit()
        el.save_commit(g, opt.branch, merged_commit=b_id,
                       msg='merged from %s:%s..%s on %s'
                         % (opt.merge, a_id, b_id, time.asctime()))
    
    g.flush()
 
