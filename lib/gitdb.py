# a lame substitute for what git would do if we had it, but in sqlite form.
# at least it's easier than rewriting git in python, or installing git on
# Windows.
import sqlite3, sha, pickle
from lib.helpers import *

_bin = sqlite3.Binary

def _selectone(db, st, args = []):
    for row in db.execute(st, args):
        return row[0]


def _create_v1(db):
    db.execute('create table Schema (version)')
    db.execute('insert into Schema default values')
    db.execute('create table Blobs (blobid primary key, zblob)')
    db.execute('create table Uuids (uuid integer primary key autoincrement)')
    db.execute('create table Trees (treeid, uuid, blobid)')
    db.execute('create index Trees_pk on Trees (treeid, uuid)')
    db.execute('create table Commits (' +
               '  commitid integer primary key autoincrement, ' +
               '  refname, merged_commit, localids, treeid)')

_schema = [(1, _create_v1)]


class GitDb:
    def __init__(self, filename):
        self.filename = filename
        self.db = sqlite3.connect(self.filename)
        try:
            sv = _selectone(self.db, 'select version from Schema')
        except sqlite3.OperationalError:
            sv = None
        for v,func in _schema:
            if v > sv:
                log('Updating to schema v%d\n' % v)
                try:
                    func(self.db)
                    self.db.execute('update Schema set version=?', [v])
                    self.db.commit()
                except:
                    try:
                        self.db.rollback()
                    except:
                        pass
                    raise
                assert(_selectone(self.db, 'select version from Schema') == v)
        self.flush()

    def flush(self):
        self.db.commit()

    def blob_set(self, content):
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        sha1 = sha.sha('blob %d\0%s' % (len(content), content)).digest()
        self.db.execute('insert or replace into Blobs (blobid,zblob) ' +
                        ' values (?,?)',
                        [_bin(sha1), _bin(content)])
        return sha1

    def blob(self, sha1):
        v = _selectone(self.db, 'select zblob from Blobs where blobid=?',
                       [_bin(sha1)])
        if v:
            return str(v)

    def uuid_new(self):
        return self.db.execute('insert into Uuids default values').lastrowid

    def _tree_encode(self, treedict):
        # git-style tree object
        s = ''
        for uuid,blobid in sorted(treedict.iteritems()):
            s += '100644 %s\0%s' % (uuid, blobid)
        return s

    def tree_set(self, treedict):
        enc = self._tree_encode(treedict)
        sha1 = sha.sha('tree %d\0%s' % (len(enc), enc)).digest()
        self.db.executemany('insert or replace into Trees ' +
                            '  (treeid, uuid, blobid)' +
                            '  values (?,?,?)',
                            ((_bin(sha1), uuid, _bin(blobid)) 
                             for uuid,blobid in treedict.iteritems()))
        return sha1

    def tree(self, treeid):
        treedict = {}
        for uuid,blobid in self.db.execute('select uuid, blobid from Trees ' +
                                           ' where treeid=?', [_bin(treeid)]):
            treedict[uuid] = str(blobid)
        return treedict

    def commit_set(self, refname, treeid, localids, merged_commit = None):
        # not at all the git format, unlike the trees and blobs
        lids = pickle.dumps([(lid,uuid) for lid,uuid in sorted(localids)])
        return self.db.execute(
                'insert into Commits ' +
                '  (refname, treeid, localids, merged_commit) ' +
                '  values (?,?,?,?)',
                [refname, _bin(treeid), _bin(lids),
                 merged_commit and _bin(merged_commit) or None]).lastrowid

    def commitid_latest(self, refname):
        return _selectone(self.db,
                          'select max(commitid) from Commits ' +
                          '  where refname=?', [refname])

    def commit(self, commitid):
        for r,t,lids,m in self.db.execute('select refname, treeid, ' +
                                   '  localids, merged_commit from Commits ' +
                                   '  where commitid=?', [commitid]):
            localids = pickle.loads(lids)
            return r,str(t),localids,m
