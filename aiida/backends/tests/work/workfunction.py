# -*- coding: utf-8 -*-

import plum.process_monitor
from aiida.backends.testbase import AiidaTestCase
from aiida.work.workfunction import workfunction
from aiida.orm.data.base import get_true_node
from aiida.work.run import async, run
import aiida.work.util as util

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


@workfunction
def simple_wf():
    return {'result': get_true_node()}


@workfunction
def return_input(inp):
    return {'result': inp}


class TestWf(AiidaTestCase):

    def setUp(self):
        super(TestWf, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestWf, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_blocking(self):
        self.assertTrue(simple_wf()['result'])
        self.assertTrue(return_input(get_true_node())['result'])

    def test_async(self):
        self.assertTrue(async(simple_wf).result()['result'])
        self.assertTrue(async(return_input, get_true_node()).result()['result'])

    def test_run(self):
        self.assertTrue(run(simple_wf)['result'])
        self.assertTrue(run(return_input, get_true_node())['result'])
