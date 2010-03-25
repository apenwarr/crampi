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


@wvtest
def test_merge_entries():
    gdb = gitdb.GitDb('test.db.tmp')
    base = Entries([])
    a1 = Entries([
        Entry('a1', 'u1', dict(a=1, b=2, c=3, d=[dict(x=7, y=9)])),
        Entry('a2', 'u2', dict(a=11, b=22, c=33, d=[dict(x=77, y=99)])),
    ])
    b1 = Entries([
        Entry('b1', 'u3', dict(a=111, b=222, c=333, d=[dict(x=777, y=999)])),
    ])
    b2 = Entries(entry.simple_merge(b1, base, a1))
    WVPASSEQ(len(b2.entries), 3)
    b2s = list(sorted(b2.entries, key=lambda i: i.uuid))
    WVPASSEQ([e.uuid for e in b2s], ['u1', 'u2', 'u3'])
    WVPASSEQ([e.lid for e in b2s], [None, None, 'b1'])
    WVPASSNE(b2s[2], b1.entries[0]) # not literally the same object
    WVPASSEQ(b2s[2].d, b1.entries[0].d)  # but the same content
    b2.entries[0].d['a'] = 1.5
    WVPASSNE(b2.entries[0].d, b1.entries[0].d)

    a2 = Entries(entry.simple_merge(a1, base, b2))
    WVPASSEQ(len(a2.entries), 3)
    a2s = list(sorted(a2.entries, key=lambda i: i.uuid))
    WVPASSEQ([e.uuid for e in a2s], ['u1', 'u2', 'u3'])
    WVPASSEQ([e.lid for e in a2s], ['a1', 'a2', None])
    a2.reindex()
    WVPASSEQ(a2.uuids['u3'].d['a'], 1.5)
