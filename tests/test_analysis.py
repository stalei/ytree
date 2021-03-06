"""
tests for analysis fields



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import numpy as np
from numpy.testing import \
    assert_array_equal
import os

from ytree.utilities.testing import \
    requires_file, \
    test_data_dir, \
    TempDirTest

import ytree

CT = os.path.join(test_data_dir,
                  "consistent_trees/tree_0_0_0.dat")

class AnalysisFieldTest(TempDirTest):
    @requires_file(CT)
    def test_analysis_fields(self):
        a = ytree.load(CT)

        a.add_analysis_field('bears', 'Msun/yr')

        fake_bears = np.zeros(a.size)
        assert_array_equal(fake_bears, a['bears'])

        a[0]['bears'] = 9
        fake_bears[0] = 9
        assert_array_equal(fake_bears, a['bears'])

        fake_tree_bears = np.zeros(a[1].tree_size)
        assert_array_equal(
            fake_tree_bears, a[1]['tree', 'bears'])
        fake_tree_bears[72] = 99
        a[1]['tree'][72]['bears'] = 99
        assert_array_equal(fake_tree_bears, a[1]['tree', 'bears'])

        fn = a.save_arbor()
        a2 = ytree.load(fn)

        assert_array_equal(fake_bears, a2['bears'])
        assert_array_equal(fake_tree_bears, a2[1]['tree', 'bears'])
