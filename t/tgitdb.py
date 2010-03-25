from wvtest import *
from lib import gitdb
from lib.helpers import *

@wvtest
def test_gitdb():
    unlink('test.db.tmp')
    g = gitdb.GitDb('test.db.tmp')
    
    b1 = g.blob_set('test\x00\x02')
    b1b = g.blob_set('test\0\x02')
    b2 = g.blob_set('hello world')
    WVPASSEQ(b1, b1b)
    WVPASSNE(b1, b2)
    WVPASSEQ(g.blob(b1), 'test\0\x02')
    WVPASSEQ(g.blob(b2), 'hello world')
    u1 = g.uuid_new()
    u1b = g.uuid_new()
    u2 = g.uuid_new()
    treedict = dict([(u1,b1), (u1b,b1b), (u2,b2)])
    t1 = g.tree_set(treedict)
    t1b = g.tree_set(treedict)
    WVPASSEQ(t1, t1b)

    td2 = g.tree(t1)
    WVPASSEQ(sorted(treedict.items()), sorted(td2.items()))

    l1 = { 9:u1, 10:u1b, 11:u2 }
    l2 = { 1:u1, 2:u1b, 3:u2 }
    c1 = g.commit_set('one', t1, l1)
    c1b = g.commit_set('one', t1, l1)
    c2 = g.commit_set('two', t1, l2)
    print c1,c1b,c2

    WVPASSNE(c1, c1b)
    WVPASSNE(c1, c2)

    WVPASSEQ(('one', t1, l1, None), g.commit(c1))
    WVPASSEQ(('one', t1, l1, None), g.commit(c1b))
    WVPASSEQ(('two', t1, l2, None), g.commit(c2))
    for r in g.db.execute('select max(commitid) from Commits where refname=?',
                          ['one']):
        print repr(r)
    WVPASSEQ(g.commitid_latest('one'), c1b)
    WVPASSEQ(g.commitid_latest('two'), c2)

    m1 = g.commit_set('two', t1, l2, c1b)
    m2 = g.commit_set('two', t1, l2, c1)
    m3 = g.commit_set('two', t1, l2, c2)
    m4 = g.commit_set('one', t1, l2, c2)
    m5 = g.commit_set('one', t1, l2, c1)

    WVPASSEQ(g.commitid_lastmerge('two', 'one'), c1)
    WVPASSEQ(g.commitid_lastmerge('two', 'two'), c2)
    WVPASSEQ(g.commitid_lastmerge('one', 'one'), c1)
    WVPASSEQ(g.commitid_lastmerge('big', 'one'), None)
    WVPASSEQ(g.commitid_lastmerge('one', 'stupid'), None)
    WVPASSEQ(g.commitid_lastmerge('bill', 'fred'), None)
    
    g.flush()
    
