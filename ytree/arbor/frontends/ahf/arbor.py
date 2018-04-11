"""
AHFArbor class and member functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import glob
import os

from yt.units.yt_array import \
    UnitParseError

from ytree.arbor.arbor import \
    CatalogArbor
from ytree.arbor.frontends.ahf.fields import \
    AHFFieldInfo
from ytree.arbor.frontends.ahf.io import \
    AHFDataFile

class AHFArbor(CatalogArbor):
    """
    Class for Arbors created from AHF out_*.list files.
    Use only descendent IDs to determine tree relationship.
    """

    _suffix = ".list"
    _field_info_class = AHFFieldInfo
    _data_file_class = AHFDataFile

    def _parse_parameter_file(self):
        self.field_list = []
        return
        fgroups = setup_field_groups()
        rems = ["%s%s%s" % (s[0], t, s[1])
                for s in [("(", ")"), ("", "")]
                for t in ["physical, peculiar",
                          "comoving", "physical"]]

        f = open(self.filename, "r")
        # Read the first line as a list of all fields.
        fields = f.readline()[1:].strip().split()

        # Get box size, cosmological parameters, and units.
        while True:
            line = f.readline()
            if line is None or not line.startswith("#"):
                break
            elif line.startswith("#Om = "):
                pars = line[1:].split(";")
                for j, par in enumerate(["omega_matter",
                                         "omega_lambda",
                                         "hubble_constant"]):
                    v = float(pars[j].split(" = ")[1])
                    setattr(self, par, v)
            elif line.startswith("#Box size:"):
                pars = line.split(":")[1].strip().split()
                self.box_size = self.quan(float(pars[0]), pars[1])
            # Looking for <quantities> in <units>
            elif line.startswith("#Units:"):
                if " in " not in line: continue
                quan, punits = line[8:].strip().split(" in ", 2)
                for rem in rems:
                    while rem in punits:
                        pre, mid, pos = punits.partition(rem)
                        punits = pre + pos
                try:
                    self.quan(1, punits)
                except UnitParseError:
                    punits = ""
                for group in fgroups:
                    if group.in_group(quan):
                        group.units = punits
                        break
        f.close()

        fi = {}
        for i, field in enumerate(fields):
            for group in fgroups:
                units = ""
                if group.in_group(field):
                    units = getattr(group, "units", "")
                    break
            fi[field] = {"column": i, "units": units}

        # the scale factor comes from the catalog file header
        fields.append("scale_factor")
        fi["scale_factor"] = {"column": "header", "units": ""}

        self.field_list = fields
        self.field_info.update(fi)

    def _set_units(self):
        pass

    def _get_data_files(self):
        pass
    #     """
    #     Get all out_*.list files and sort them in reverse order.
    #     """
    #     prefix = self.filename.rsplit("_", 1)[0]
    #     suffix = self._suffix
    #     my_files = glob.glob("%s_*%s" % (prefix, suffix))
    #     # sort by catalog number
    #     my_files.sort(
    #         key=lambda x:
    #         self._get_file_index(x, prefix, suffix),
    #         reverse=True)
    #     self.data_files = \
    #       [self._data_file_class(f, self) for f in my_files]

    # def _get_file_index(self, f, prefix, suffix):
    #     return int(f[f.find(prefix)+len(prefix)+1:f.rfind(suffix)]),

    @classmethod
    def _is_valid(self, *args, **kwargs):
        """
        File must end in .AHF_halos and have an associated
        .parameter file.
        """
        fn = args[0]
        if not fn.endswith(".AHF_halos"):
            return False
        key = fn[:fn.rfind(".z")]
        if not os.path.exists(key + ".parameter"):
            return False
        return True
