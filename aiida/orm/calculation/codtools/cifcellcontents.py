# -*- coding: utf-8 -*-
"""
Plugin to create input for scripts from cod-tools package.
This plugin is in the development stage. Andrius Merkys, 2014-10-29
"""
import os
import shutil

from aiida.orm.calculation.codtools import CodtoolsCalculation

__copyright__ = u"Copyright (c), 2014, École Polytechnique Fédérale de Lausanne (EPFL), Switzerland, Laboratory of Theory and Simulation of Materials (THEOS). All rights reserved."
__license__ = "Non-Commercial, End-User Software License Agreement, see LICENSE.txt file"
__version__ = "0.2.1"

class CifcellcontentsCalculation(CodtoolsCalculation):
    """
    Specific input plugin for cif_cell_contents from cod-tools package.
    """

    def _init_internal_params(self):
        super(CifcellcontentsCalculation, self)._init_internal_params()

        self._default_parser = 'codtools.cifcellcontents'