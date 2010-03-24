from wvtest import *
from lib import entry, gitdb
from lib.entry import Entry, Entries

@wvtest
def test_save_load_entries():
    gdb = gitdb.GitDb('test.db.tmp')
    e1 = Entries([
        Entry('l1', 'u1', dict(a=1, b=2, c=3, d=[dict(x=7, y=9)])),
        Entry('l2', None, dict(a=11, b=22, c=33, d=[dict(x=77, y=99)])),
    ])
    try:
        e1.save_commit(gdb, 'tsle')
    except:
        WVPASS("expected exception")
    else:
        WVFAIL("expected exception")
    e1.assign_missing_uuids(gdb)
    c1 = e1.save_commit(gdb, 'tsle')
    WVPASS(c1)
    WVPASSEQ(gdb.commitid_latest('tsle'), c1)
    c1b = e1.save_commit(gdb, 'tsle')
    WVPASS(c1b)
    WVPASSNE(c1, c1b)
    WVPASSEQ(gdb.commitid_latest('tsle'), c1b)
    t1 = e1.save_tree(gdb)

    (r1a, t1a, lids1a, m1a) = gdb.commit(c1)
    (r1b, t1b, lids1b, m1b) = gdb.commit(c1b)
    WVPASSEQ(t1, t1a)
    WVPASSEQ(t1, t1b)
    WVPASSEQ(r1a, 'tsle')
    WVPASSEQ(r1b, 'tsle')
    WVPASSEQ(lids1a, lids1b)
    WVPASSEQ(lids1a, dict(l1='u1', l2=e1.entries[1].uuid))
    e1.reindex()
    WVPASSEQ(len(e1.lids), 2)
    WVPASSEQ(len(e1.uuids), 2)
    WVPASSEQ(e1.lids['l2'], e1.entries[1])
    WVPASSEQ(e1.lids['l1'], e1.entries[0])
    WVPASSEQ(e1.uuids['u1'], e1.entries[0])

    (u1, u2) = (e1.lids['l1'].uuid, e1.lids['l2'].uuid)
    e2 = entry.load_tree(gdb, t1)
    e2.reindex()
    WVPASSEQ(e2.uuids[u1].d, e1.uuids[u1].d)
    WVPASSEQ(e2.uuids[u2].d, e1.uuids[u2].d)

