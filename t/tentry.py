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
