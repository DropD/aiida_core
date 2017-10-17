# -*- coding: utf-8 -*-
# pylint: disable=protected-access
"""Functionality tests for verdi commands"""
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import unittest

import mock
from click.testing import CliRunner

from aiida.backends.testbase import AiidaTestCase
from aiida.common.datastructures import calc_states
from aiida.utils.capturing import Capturing

# Common computer information
COMPUTER_COMMON_INFO = [
    "localhost",
    "",
    "True",
    "ssh",
    "torque",
    "/scratch/{username}/aiida_run",
    "mpirun -np {tot_num_mpiprocs}",
    "1",
    EOFError,
    EOFError,
]

# Computer #1
COMPUTER_NAME_1 = "torquessh1"
COMPUTER_SETUP_INPUT_1 = [COMPUTER_NAME_1] + COMPUTER_COMMON_INFO

# Computer #2
COMPUTER_NAME_2 = "torquessh2"
COMPUTER_SETUP_INPUT_2 = [COMPUTER_NAME_2] + COMPUTER_COMMON_INFO

# Common code information
CODE_COMMON_INFO_1 = [
    "simple script",
    "False",
    "simpleplugins.templatereplacer",
]
CODE_COMMON_INFO_2 = [
    "/usr/local/bin/doubler.sh",
    EOFError,
    EOFError,
]

# Code #1
CODE_NAME_1 = "doubler_1"
CODE_SETUP_INPUT_1 = (
    [CODE_NAME_1] + CODE_COMMON_INFO_1 + [COMPUTER_NAME_1] + CODE_COMMON_INFO_2)
# Code #2
CODE_NAME_2 = "doubler_2"
CODE_SETUP_INPUT_2 = (
    [CODE_NAME_2] + CODE_COMMON_INFO_1 + [COMPUTER_NAME_2] + CODE_COMMON_INFO_2)


class TestVerdiCalculationCommands(AiidaTestCase):
    # pylint: disable=missing-docstring

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create some calculations with various states
        """
        super(TestVerdiCalculationCommands, cls).setUpClass()

        from aiida.orm import JobCalculation

        # Create some calculation
        calc1 = JobCalculation(
            computer=cls.computer,  # pylint: disable=no-member
            resources={'num_machines': 1,
                       'num_mpiprocs_per_machine': 1}).store()
        calc1._set_state(calc_states.TOSUBMIT)
        calc2 = JobCalculation(
            computer=cls.computer.name,  # pylint: disable=no-member
            resources={'num_machines': 1,
                       'num_mpiprocs_per_machine': 1}).store()
        calc2._set_state(calc_states.COMPUTED)
        calc3 = JobCalculation(
            computer=cls.computer.id,  # pylint: disable=no-member
            resources={'num_machines': 1,
                       'num_mpiprocs_per_machine': 1}).store()
        calc3._set_state(calc_states.FINISHED)

    def test_calculation_list(self):
        """
        Do some calculation listing to ensure that verdi calculation list
        works and gives at least to some extent the expected results.
        """
        from aiida.cmdline.commands.calculation import Calculation
        calc_cmd = Calculation()

        with Capturing() as output:
            calc_cmd.calculation_list()

        out_str = ''.join(output)
        self.assertTrue(calc_states.TOSUBMIT in out_str,
                        "The TOSUBMIT calculations should be part fo the "
                        "simple calculation list.")
        self.assertTrue(calc_states.COMPUTED in out_str,
                        "The COMPUTED calculations should be part fo the "
                        "simple calculation list.")
        self.assertFalse(calc_states.FINISHED in out_str,
                         "The FINISHED calculations should not be part fo the "
                         "simple calculation list.")

        with Capturing() as output:
            calc_cmd.calculation_list(* ['-a'])

        out_str = ''.join(output)
        self.assertTrue(calc_states.FINISHED in out_str,
                        "The FINISHED calculations should be part fo the "
                        "simple calculation list.")


# pylint: disable=no-value-for-parameter
@unittest.skip('changes in code setup')
class TestVerdiCodeCommands(AiidaTestCase):
    # pylint: disable=missing-docstring

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create the computers and setup a codes
        """
        super(TestVerdiCodeCommands, cls).setUpClass()

        # Setup computer #1
        from aiida.cmdline.commands.computer import Computer
        cmd_comp = Computer()
        with mock.patch(
                '__builtin__.raw_input', side_effect=COMPUTER_SETUP_INPUT_1):
            with Capturing():
                cmd_comp.computer_setup()

        # Setup a code for computer #1
        from aiida.cmdline.commands.code import code_setup
        with mock.patch(
                '__builtin__.raw_input', side_effect=CODE_SETUP_INPUT_1):
            with Capturing():
                code_setup()

        # Setup computer #2
        with mock.patch(
                '__builtin__.raw_input', side_effect=COMPUTER_SETUP_INPUT_2):
            with Capturing():
                cmd_comp.computer_setup()

        # Setup a code for computer #2
        with mock.patch(
                '__builtin__.raw_input', side_effect=CODE_SETUP_INPUT_2):
            with Capturing():
                code_setup()

    def test_code_list(self):
        """
        Do some code listing test to ensure the correct behaviour of
        verdi code list
        """
        from aiida.cmdline.commands.code import Code
        code_cmd = Code()

        # Run a simple verdi code list, capture the output and check the result
        with Capturing() as output:
            code_cmd.code_list()
        out_str_1 = ''.join(output)
        self.assertTrue(COMPUTER_NAME_1 in out_str_1,
                        "The computer 1 name should be included into "
                        "this list")
        self.assertTrue(CODE_NAME_1 in out_str_1,
                        "The code 1 name should be included into this list")
        self.assertTrue(COMPUTER_NAME_2 in out_str_1,
                        "The computer 2 name should be included into "
                        "this list")
        self.assertTrue(CODE_NAME_2 in out_str_1,
                        "The code 2 name should be included into this list")

        # Run a verdi code list -a, capture the output and check if the result
        # is the same as the previous one
        with Capturing() as output:
            code_cmd.code_list(* ['-a'])
        out_str_2 = ''.join(output)
        self.assertEqual(out_str_1, out_str_2,
                         "verdi code list & verdi code list -a should provide "
                         "the same output in this experiment.")

        # Run a verdi code list -c, capture the output and check the result
        with Capturing() as output:
            code_cmd.code_list(* ['-c', COMPUTER_NAME_1])
        out_str = ''.join(output)
        self.assertTrue(COMPUTER_NAME_1 in out_str,
                        "The computer 1 name should be included into "
                        "this list")
        self.assertFalse(COMPUTER_NAME_2 in out_str,
                         "The computer 2 name should not be included into "
                         "this list")


class TestVerdiWorkCommands(AiidaTestCase):
    # pylint: disable=missing-docstring

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """
        Create a simple workchain and run it.
        """
        super(TestVerdiWorkCommands, cls).setUpClass()
        from aiida.work.run import run
        from aiida.work.workchain import WorkChain
        test_string = 'Test report.'
        cls.test_string = test_string

        class Wf(WorkChain):
            # pylint: disable=missing-docstring,abstract-method

            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                spec.outline(cls.create_logs)

            def create_logs(self):
                self.report(test_string)

        _, cls.workchain_pid = run(Wf, _return_pid=True)

    def test_report(self):
        """
        Test that 'verdi work report' contains the report message.
        """
        from aiida.cmdline.commands.work import report

        result = CliRunner().invoke(
            report, [str(self.workchain_pid)], catch_exceptions=False)
        self.assertTrue(self.test_string in result.output)

    def test_report_debug(self):
        """
        Test that 'verdi work report' contains the report message when called with levelname DEBUG.
        """
        from aiida.cmdline.commands.work import report

        result = CliRunner().invoke(
            report, [str(self.workchain_pid), '--levelname', 'DEBUG'],
            catch_exceptions=False)
        self.assertTrue(self.test_string in result.output)

    def test_report_error(self):
        """
        Test that 'verdi work report' does not contain the report message when called with levelname ERROR.
        """
        from aiida.cmdline.commands.work import report

        result = CliRunner().invoke(
            report, [str(self.workchain_pid), '--levelname', 'ERROR'],
            catch_exceptions=False)
        self.assertTrue(self.test_string not in result.output)
