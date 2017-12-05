"""Database persister to persist plumpy command states and context in the AiiDA db as JobCalculation attributes."""
from aiida.orm import load_node
from plum import Bundle
from plum.persistence import Persister


class DatabasePersister(Persister):
    """Persist Process state in Calculation db nodes."""

    def save_checkpoint(self, process, tag=None):
        """
        Persist a process to it's calculation node.

        :param process: :class:`aiida.work.legacy.job_process.JobProcess`
        :param tag: optional tag to this specific checkpoint. Ignored for now.
        """
        bundle = Bundle(process)
        process.calc._set_attr('checkpoint', bundle)  # pylint: disable=protected-access

    def load_checkpoint(self, pid, tag=None):
        return load_node(pid).get_attr('checkpoint')

    def delete_checkpoint(self, pid, tag=None):
        raise NotImplementedError

    def delete_process_checkpoints(self, pid):
        raise NotImplementedError

    def get_checkpoints(self):
        raise NotImplementedError

    def get_process_checkpoints(self, pid):
        raise NotImplementedError
