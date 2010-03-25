import yaml, copy

class Entry:
    def __init__(self, lid, uuid, d):
        self.lid = lid
        self.uuid = uuid
        self.d = d

    def to_yaml(self):
        return yaml.safe_dump(self.d, default_flow_style=False)


class Entries:
    def __init__(self, entries):
        self.entries = list(entries)
        self.lids = self.uuids = None  # no indexes by default

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


def merge(main, merged):
    r = Entries([])
    seen = {}
    for e in main.entries:
        ne = Entry(e.lid, e.uuid, copy.deepcopy(e.d))
        r.entries.append(ne)
        seen[e.uuid] = ne
    for e in merged.entries:
        if e.uuid in seen:
            seen[e.uuid].d = copy.deepcopy(e.d)
        else:
            r.entries.append(Entry(None, e.uuid, copy.deepcopy(e.d)))
    return r
