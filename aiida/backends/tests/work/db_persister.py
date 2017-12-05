# pylint: disable=astroid-error
"""Unit test the :class:`aiida.work.db_persister.DatabasePersister` class."""
from aiida.backends.testbase import AiidaTestCase
from aiida.work import WorkChain
from aiida.work.db_persister import DatabasePersister


class TestWorkchain(WorkChain):
    """Simple Workchain for testing the DatabasePersister."""

    @classmethod
    def define(cls, spec):
        super(TestWorkchain, cls).define(spec)
        spec.input('a')
        spec.input('b')
        spec.dynamic_output()
        spec.outline(cls.square_a, cls.sum_a_b)

    def square_a(self):
        self.ctx.a_squared = self.inputs.a.value**2

    def sum_a_b(self):
        self.ctx.sum = self.inputs.b.value + self.ctx.a_squared


class TestDatabasePersister(AiidaTestCase):
    # pylint: disable=missing-docstring

    def test_save_load_roundtrip(self):
        """Test saving, retrieving and recreating a checkpoint."""

        process = TestWorkchain(inputs={'a': 2, 'b': 4})
        persister = DatabasePersister()
        persister.save_checkpoint(process)

        bundle = persister.load_checkpoint(process.pid)
        recreated = bundle.unbundle()
        self.assertEqual(recreated.inputs.a.value, 2)
        self.assertEqual(recreated.inputs.b.value, 4)
