import yaml, copy

class Entry:
    def __init__(self, lid, uuid, d):
        self.lid = lid
        self.uuid = uuid
        self.d = copy.copy(d)

    def __unicode__(self):
        return '%s: %s %s' % (self.uuid, self.d.get('firstname', 'Mr.'),
                              self.d.get('lastname', 'Noname'))

    def __str__(self):
        try:
            return str(self.__unicode__())
        except UnicodeEncodeError:
            return repr(self.__unicode__())

    def to_yaml(self):
        return yaml.safe_dump(self.d, default_flow_style=False)

    def patch(self, ad, bd):
        if not ad:
            ad = {}
        for k in set(ad.keys()) | set(bd.keys()):
            av = ad.get(k)
            bv = bd.get(k)
            if av != bv:
                print 'updating %r from %r to %r' % (k, self.d.get(k), bv)
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

    def uuids_from_commit(self, gdb, refname):
        commitid = gdb.commitid_latest(refname)
        if commitid:
            (r, tree, localids, merged_commit) = gdb.commit(commitid)
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
            blobs[e.uuid] = gdb.blob_set(e.to_yaml())
        return gdb.tree_set(blobs)

    def save_commit(self, gdb, refname, merged_commit = None):
        localids = []
        for e in self.entries:
            assert(e.lid)
            assert(e.uuid)
            localids.append((e.lid, e.uuid))
        return gdb.commit_set(refname, self.save_tree(gdb), localids,
                              merged_commit = merged_commit)


def _load_tree(gdb, treeid):
    for (uuid,blobid) in gdb.tree(treeid).iteritems():
        d = yaml.safe_load(gdb.blob(blobid))
        yield Entry(None,uuid,d)


def load_tree(gdb, treeid):
    return Entries(_load_tree(gdb, treeid))


def load_tree_from_commit(gdb, commitid):
    rv = gdb.commit(commitid)
    if rv:
        (ref, treeid, localids, m) = gdb.commit(commitid)
        return load_tree(gdb, treeid)
    else:
        return Entries([])
    

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


def simple_merge(cur, a, b):
    for lid,uuid,ed,aed,bed in merge(cur, a, b):
        if aed and not bed:
            # deleted
            pass
        elif bed and (not aed or aed != bed):
            yield Entry(lid, uuid, bed)
        else:
            yield Entry(lid, uuid, ed)
