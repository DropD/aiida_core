# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"


import uuid
import shutil
import tempfile
import threading

import plum.process_monitor
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import load_node
from aiida.orm.data.base import Int
from aiida.work.persistence import Persistence
from aiida.work.process import Process, FunctionProcess
from aiida.work.run import run, submit
import aiida.work.util as util
from aiida.work.test_utils import DummyProcess, BadOutput
from aiida.common.lang import override


class ProcessStackTest(Process):

    @override
    def _run(self):
        pass

    @override
    def on_create(self, pid, inputs, saved_instance_state):
        super(ProcessStackTest, self).on_create(
            pid, inputs, saved_instance_state)
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        # The therad must match the one used in on_create because process
        # stack is using thread local storage to keep track of who called who
        super(ProcessStackTest, self).on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess(AiidaTestCase):

    def setUp(self):
        super(TestProcess, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestProcess, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_process_stack(self):
        ProcessStackTest.run()

    def test_inputs(self):
        with self.assertRaises(AssertionError):
            BadOutput.run()

    def test_pid_is_uuid(self):
        p = DummyProcess.new_instance(inputs={'_store_provenance': False})
        self.assertEqual(uuid.UUID(p._calc.uuid), p.pid)
        p.stop()
        p.run_until_complete()

    def test_input_link_creation(self):
        dummy_inputs = ["1", "2", "3", "4"]

        inputs = {l: Int(l) for l in dummy_inputs}
        inputs['_store_provenance'] = True
        p = DummyProcess.new_instance(inputs)

        for label, value in p._calc.get_inputs_dict().iteritems():
            self.assertTrue(label in inputs)
            self.assertEqual(int(label), int(value.value))
            dummy_inputs.remove(label)

        # Make sure there are no other inputs
        self.assertFalse(dummy_inputs)

        p.stop()
        p.run_until_complete()

    def test_none_input(self):
        # Check that if we pass no input the process runs fine
        DummyProcess.new_instance().run_until_complete()
        # Check that if we explicitly pass None as the input it also runs fine
        DummyProcess.new_instance(inputs=None).run_until_complete()

    def test_seal(self):
        pid = run(DummyProcess, _return_pid=True)[1]
        self.assertTrue(load_node(pk=pid).is_sealed)

        storedir = tempfile.mkdtemp()
        storage = Persistence.create_from_basedir(storedir)

        pid = submit(DummyProcess, _jobs_store=storage)
        n = load_node(pk=pid)
        self.assertFalse(n.is_sealed)

        dp = DummyProcess.create_from(storage.load_checkpoint(pid))
        dp.run_until_complete()
        self.assertTrue(n.is_sealed)
        shutil.rmtree(storedir)

    def test_description(self):
        dp = DummyProcess.new_instance(inputs={'_description': 'My description'})
        self.assertEquals(dp.calc.description, 'My description')
        dp.run_until_complete()

        with self.assertRaises(ValueError):
            DummyProcess.new_instance(inputs={'_description': 5})

    def test_label(self):
        dp = DummyProcess.new_instance(inputs={'_label': 'My label'})
        self.assertEquals(dp.calc.label, 'My label')
        dp.run_until_complete()

        with self.assertRaises(ValueError):
            DummyProcess.new_instance(inputs={'_label': 5})


class TestFunctionProcess(AiidaTestCase):

    def test_fixed_inputs(self):
        def wf(a, b, c):
            return {'a': a, 'b': b, 'c': c}

        inputs = {'a': Int(4), 'b': Int(5), 'c': Int(6)}
        FP = FunctionProcess.build(wf)
        self.assertEqual(FP.run(**inputs), inputs)

    def test_kwargs(self):
        def wf_with_kwargs(**kwargs):
            return kwargs

        def wf_without_kwargs():
            return Int(4)

        def wf_fixed_args(a):
            return {'a': a}

        a = Int(4)
        inputs = {'a': a}

        FP = FunctionProcess.build(wf_with_kwargs)
        outs = FP.run(**inputs)
        self.assertEqual(outs, inputs)

        FP = FunctionProcess.build(wf_without_kwargs)
        with self.assertRaises(ValueError):
            FP.run(**inputs)

        FP = FunctionProcess.build(wf_fixed_args)
        outs = FP.run(**inputs)
        self.assertEqual(outs, inputs)
