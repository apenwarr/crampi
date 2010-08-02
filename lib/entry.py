import copy
from lib import ycoder

class Entry:
    def __init__(self, lid, uuid, d):
        self.lid = lid
        self.uuid = uuid
        self.d = copy.copy(d)

    def __unicode__(self):
        fn = self.d.get('firstname')
        ln = self.d.get('lastname')
        cn = self.d.get('company')
        if fn or ln:
            return '%s: %s %s' % (self.uuid, fn, ln)
        else:
            return '%s: *%s' % (self.uuid, cn)

    def __str__(self):
        try:
            return str(self.__unicode__())
        except UnicodeEncodeError:
            return repr(self.__unicode__())

    def encode(self):
        return ycoder.encode(self.d)

    def patch(self, ad, bd):
        if not ad:
            ad = {}
        for k in set(ad.keys()) | set(bd.keys()):
            av = ad.get(k)
            bv = bd.get(k)
            ev = self.d.get(k)
            if av != bv and ev != bv:
                print 'updating %r from %r to %r' % (k, ev, bv)
                self.d[k] = bv


class Entries:
    def __init__(self, entries):
        self.entries = list(entries)
        self.lids = self.uuids = None  # no indexes by default

    def clone(self):
        return Entries([Entry(e.lid,e.uuid,copy.copy(e.d))
                        for e in self.entries])

    def reindex(self):
        self.lids = {}
        self.uuids = {}
        for e in self.entries:
            if e.uuid:
                assert(not e.uuid in self.uuids)
                self.uuids[e.uuid] = e
            if e.lid:
                assert(not e.lid in self.lids)
                self.lids[e.lid] = e

    # match the lid for each entry with the lid from a previous commit, and
    # copy the uuids from there.  That's how we make sure the uuids end up
    # the same every time.
    def uuids_from_commit(self, gdb, refname):
        commitid = gdb.commitid_latest(refname)
        if commitid:
            (r, tree, localids, msg, merged_commit) = gdb.commit(commitid)
            for e in self.entries:
                if not e.uuid:
                    e.uuid = localids.get(e.lid)

    def assign_missing_uuids(self, gdb):
        for e in self.entries:
            if not e.uuid:
                e.uuid = gdb.uuid_new()

    def save_tree(self, gdb):
        blobs = {}
        for e in self.entries:
            assert(e.uuid)
            assert(e.lid)
            blobs[e.uuid] = gdb.blob_set(e.encode())
        return gdb.tree_set(blobs)

    def save_commit(self, gdb, refname, msg, merged_commit = None):
        localids = []
        for e in self.entries:
            assert(e.lid)
            assert(e.uuid)
            localids.append((e.lid, e.uuid))
        return gdb.commit_set(refname, self.save_tree(gdb), localids, msg,
                              merged_commit = merged_commit)


def _load_tree(gdb, treeid, localids_rev):
    for (uuid,blobid) in gdb.tree(treeid).iteritems():
        d = ycoder.decode(gdb.blob(blobid))
        yield Entry(localids_rev[uuid],uuid,d)


def load_tree(gdb, treeid, localids_rev):
    return Entries(_load_tree(gdb, treeid, localids_rev))


def load_tree_from_commit(gdb, commitid):
    rv = gdb.commit(commitid)
    if rv:
        (ref, treeid, localids, msg, m) = gdb.commit(commitid)
        localids_rev = {}
        for lid,uuid in localids.items():
            localids_rev[uuid] = lid
        return load_tree(gdb, treeid, localids_rev)
    else:
        return Entries([])
    

# do a three-way merge of Entries objects cur, a, and b.
# The result corresponds to a 3-way diff that applies the changes from a->b
# into cur. For each uuid that occurs in any of the three, yields
# the lid, uuid, and three dictionaries needed to complete a column-by-column
# merge if you want.  (If you just want to use last-writer-wins on the
# entire record, use simple_merge().)
def merge(cur, a, b):
    cur.reindex()
    a.reindex()
    b.reindex()
    added = set(b.uuids.keys()) - set(a.uuids.keys()) - set(cur.uuids.keys())
    for e in cur.entries:
        ae = a.uuids.get(e.uuid)
        be = b.uuids.get(e.uuid)
        yield (e.lid, e.uuid, 
               e.d,
               ae and ae.d or None,
               be and be.d or None)
    for uuid in added:
        be = b.uuids.get(uuid)
        yield (None, uuid,
               None, None, be.d)


# a "two-way diff" algorithm, which we implement as a special case of the
# three-way diff.  Just return the uuid and dictionaries of each item that
# occurs in either Entries object.
def diff(a, b):
    for lid,uuid,ed,ad,bd in merge(a, a, b):
        yield uuid,ad,bd


# take the results of merge() and don't try to update individual subkeys;
# for each element, just use last-writer-wins across the entire object.
def simple_merge(cur, a, b):
    for lid,uuid,ed,aed,bed in merge(cur, a, b):
        if aed and not bed:
            # deleted
            pass
        elif bed and (not aed or aed != bed):
            yield Entry(lid, uuid, bed)
        else:
            yield Entry(lid, uuid, ed)
