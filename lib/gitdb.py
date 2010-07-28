# a lame substitute for what git would do if we had it, but in sqlite form.
# at least it's easier than rewriting git in python, or installing git on
# Windows.
import sqlite3, hashlib, yaml, StringIO, uuid
from lib.helpers import *

_bin = sqlite3.Binary

def _create_v1(db):
    db.execute('create table Schema (version)')
    db.execute('insert into Schema default values')
    db.execute('create table Blobs (blobid primary key, blob)')
    db.execute('create table Commits (' +
               '  commitid integer primary key autoincrement, ' +
               '  refname, tree_blobid, localids_blobid, merged_commit)')

def _update_v2(db):
    db.execute('alter table Commits add msg')

_schema = [(1, _create_v1),
           (2, _update_v2)]


class GitDb:
    def __init__(self, filename):
        self.filename = filename
        self.db = sqlite3.connect(self.filename)
        try:
            sv = selectone(self.db, 'select version from Schema')
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
                assert(selectone(self.db, 'select version from Schema') == v)
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
        v = selectone(self.db, 'select blob from Blobs where blobid=?',
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

    def commit_set(self, refname, treeid, localids, msg, merged_commit = None):
        # not at all the git format, unlike the trees and blobs
        lids = yaml.safe_dump(dict(localids))
        lb = self.blob_set(lids)
        return self.db.execute(
                'insert into Commits ' +
                '  (refname, tree_blobid, localids_blobid, ' + 
                '   msg, merged_commit) ' +
                '  values (?,?,?,?,?)',
                [refname, treeid, lb, msg, merged_commit]).lastrowid

    def commitid_latest(self, refname):
        return selectone(self.db,
                          'select max(commitid) from Commits ' +
                          '  where refname=?', [refname])

    def commitid_lastmerge(self, refname, merged_refname):
        return selectone(self.db,
                          'select p2.commitid ' +
                          '  from Commits p1, Commits p2 ' +
                          '  where p1.merged_commit = p2.commitid ' +
                          '  and p1.refname=? and ' +
                          '      p2.refname=? ' +
                          '  order by p1.commitid desc ' +
                          '  limit 1',
                          [refname, merged_refname])
        
    def commit(self, commitid):
        for r,t,lb,msg,m in self.db.execute('select refname, tree_blobid, ' +
                                   '  localids_blobid, msg, merged_commit ' +
                                   '  from Commits ' +
                                   '  where commitid=?', [commitid]):
            lids = self.blob(lb)
            localids = yaml.safe_load(StringIO.StringIO(lids))
            return r,str(t),localids,msg,m
