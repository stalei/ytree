import numpy as np
import yt

class SimpleKnot(object):
    def __init__(self, halo_id, properties=None):
        self.halo_id = halo_id
        self.ancestors = None
        if properties is None: properties = {}
        for p, val in properties.items():
            setattr(self, p, val)

    def __repr__(self):
        return "SimpleKnot[%d]" % self.halo_id

def get_ancestry_arrays(knot, fields):
    data = dict([(field, []) for field in fields])
    my_knot = knot
    while my_knot is not None:
        for field in fields:
            data[field].append(getattr(my_knot, field))
        if my_knot.ancestors is not None and \
          len(my_knot.ancestors) > 0:
            my_knot = my_knot.ancestors[0]
        else:
            my_knot = None
    for field in data:
        data[field] = yt.YTArray(data[field])
    return data

def load_tree(filename, properties=None):
    ds = yt.load(filename)
    if properties is None: properties = {}

    halo_ids = ds.data["halo_ids"].d.astype(np.int64)
    ancestor_counts = ds.data["ancestor_counts"].d.astype(np.int64)

    # 1) Get the number of ancestors on each level.
    level_count = []
    i_count = 0
    knots_on_level = 1
    pbar = yt.get_pbar("Calculating levels", ancestor_counts.size)
    while (i_count < ancestor_counts.size):
        level_count.append(ancestor_counts[i_count:i_count+knots_on_level])
        i_count += knots_on_level
        knots_on_level = level_count[-1].sum()
        pbar.update(i_count)
    pbar.finish()

    # 2) Create level arrays full of knots.
    i_halo = 0
    level_knots = []
    pbar = yt.get_pbar("Creating knots", halo_ids.size)
    for i_level, level in enumerate(level_count):
        level_knots.append([])
        for i_on_level in range(sum(level)):
            halo_properties = dict([(hp, ds.data[hp][i_halo])
                                    for hp in properties])
            halo_properties["redshift"] = ds.data["redshift"][i_level]
            my_id = halo_ids[i_halo]
            level_knots[-1].append(SimpleKnot(halo_ids[i_halo],
                                              halo_properties))
            i_halo += 1
            pbar.update(i_halo)
    pbar.finish()
    level_count.pop(0)

    # 3) Assemble tree structure.
    pbar = yt.get_pbar("Assembling tree", len(level_knots[:-1]))
    for i_level, knots in enumerate(level_knots[:-1]):
        i_anc = 0
        for i_knot, knot in enumerate(knots):
            n_anc = level_count[i_level][i_knot]
            knot.ancestors = level_knots[i_level+1][i_anc:i_anc+n_anc]
            i_anc += n_anc
        pbar.update(i_level)
    pbar.finish()
    
    my_tree = level_knots.pop(0)
    del level_knots
    return my_tree