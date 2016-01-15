import numpy as np
import yt

from yt.utilities.exceptions import \
    YTSphereTooSmall

def halos_in_sphere(hc, ds2, radius_field, factor=1):
    radius = (factor * hc[radius_field]).in_units("code_length")
    try:
        sp = ds2.sphere(hc.position.in_units("code_length"), radius)
        my_ids = sp[(hc.ptype, "particle_identifier")]
        return my_ids.d.astype(np.int64)
    except YTSphereTooSmall:
        return []

def simple_ancestry(hc, candidate):
    threshold = 0.5
    hc_ids = hc["member_ids"]
    c_ids = candidate["member_ids"]
    common = np.intersect1d(hc_ids, c_ids)
    return common.size > threshold * c_ids.size

class SimpleHalo(object):
    def __init__(self, halo_type, halo_id, halo_info=None):
        self.halo_type = halo_type
        self.halo_id = halo_id
        self.ancestors = None
        if halo_info is None:
            halo_info = {}
        for key, value in halo_info.items():
            setattr(self, key, value)

class SimpleTree(object):
    def __init__(self, time_series):
        self.ts = time_series

    def find_ancestors(self, hc, ds2):
        ancestors = []
        candidate_ids = halos_in_sphere(hc, ds2, "Group_R_Crit200", 5)
        for candidate_id in candidate_ids:
            candidate = ds2.halo(hc.ptype, candidate_id)
            if simple_ancestry(hc, candidate):
                ancestors.append(candidate_id)
        return ancestors

    def trace_lineage(self, halo_type, halo_id):
        ds2 = None
        current_halos = None
        for i in range(len(self.ts.outputs)-1, 1, -1):
            next_halos = []
            if ds2 is None:
                ds1 = yt.load(self.ts.outputs[i])
            else:
                ds1 = ds2                
            ds2 = yt.load(self.ts.outputs[i-1])

            if current_halos is None:
                trunk = SimpleHalo(
                    halo_type, halo_id,
                    halo_info={"redshift": ds1.current_redshift,
                               "ds": ds1.parameter_filename})
                current_halos = [trunk]

            yt.mylog.info("Creating halo ancestries for z = %f to %f." %
                          (ds1.current_redshift, ds2.current_redshift))

            for current_halo in current_halos:
                yt.mylog.info("Searching for ancestors of halo %d." %
                              current_halo.halo_id)
                hc = ds1.halo(current_halo.halo_type,
                              current_halo.halo_id)
                ancestor_ids = self.find_ancestors(hc, ds2)
                ancestor_info = {"redshift": ds2.current_redshift,
                                 "ds": ds2.parameter_filename}
                ancestor_halos = \
                  [SimpleHalo(halo_type, ancestor_id, ancestor_info)
                   for ancestor_id in ancestor_ids]
                yt.mylog.info("Halo %d has %d ancestors." %
                              (current_halo.halo_id, len(ancestor_ids)))
                current_halo.ancestors = ancestor_halos
                next_halos.extend(ancestor_halos)

            current_halos = next_halos
            if len(current_halos) == 0:
                break

        return trunk
