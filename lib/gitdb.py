# a lame substitute for what git would do if we had it, but in sqlite form.
# at least it's easier than rewriting git in python, or installing git on
# Windows.
import sqlite3, hashlib, yaml, StringIO, uuid
from lib.helpers import *

_bin = sqlite3.Binary

def _selectone(db, st, args = []):
    for row in db.execute(st, args):
        return row[0]


def _create_v1(db):
    db.execute('create table Schema (version)')
    db.execute('insert into Schema default values')
    db.execute('create table Blobs (blobid primary key, blob)')
    db.execute('create table Commits (' +
               '  commitid integer primary key autoincrement, ' +
               '  refname, tree_blobid, localids_blobid, merged_commit)')

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

    def _blob_set(self, type, content):
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        sha1 = hashlib.sha1('blob %d\0%s' % (len(content), content)).hexdigest()
        self.db.execute('insert or replace into Blobs (blobid,blob) ' +
                        ' values (?,?)',
                        [sha1, _bin(content)])
        return sha1

    def blob_set(self, content):
        return self._blob_set('blob', content)

    def blob(self, sha1):
        v = _selectone(self.db, 'select blob from Blobs where blobid=?',
                       [sha1])
        if v:
            return str(v)

    def uuid_new(self):
        return str(uuid.uuid4())

    def _tree_encode(self, treedict):
        # almost a git-style tree object, but not encoding in binary, so
        # it's easier to look at in sqlite
        s = ''
        for uuid,blobid in sorted(treedict.iteritems()):
            s += '100644 %s %s\n' % (uuid, blobid)
        return s

    def tree_set(self, treedict):
        return self._blob_set('tree', self._tree_encode(treedict))

    def tree(self, treeid):
        treedict = {}
        for row in self.blob(treeid).split('\n'):
            if row:
                mode,uuid,blobid = row.split(' ', 2)
                treedict[uuid] = blobid
        return treedict

    def commit_set(self, refname, treeid, localids, merged_commit = None):
        # not at all the git format, unlike the trees and blobs
        lids = yaml.safe_dump(dict(localids))
        lb = self.blob_set(lids)
        return self.db.execute(
                'insert into Commits ' +
                '  (refname, tree_blobid, localids_blobid, merged_commit) ' +
                '  values (?,?,?,?)',
                [refname, treeid, lb, merged_commit]).lastrowid

    def commitid_latest(self, refname):
        return _selectone(self.db,
                          'select max(commitid) from Commits ' +
                          '  where refname=?', [refname])

    def commit(self, commitid):
        for r,t,lb,m in self.db.execute('select refname, tree_blobid, ' +
                                   '  localids_blobid, merged_commit ' +
                                   '  from Commits ' +
                                   '  where commitid=?', [commitid]):
            lids = self.blob(lb)
            localids = yaml.safe_load(StringIO.StringIO(lids))
            return r,str(t),localids,m
