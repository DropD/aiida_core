# -*- coding: utf-8 -*-
from aiida.orm.implementation import Computer
from aiida.orm.utils import BackendDelegateWithDefault

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1"

from aiida.backends import settings
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA


class Util(BackendDelegateWithDefault):

    @classmethod
    def create_default(cls):
        if settings.BACKEND == BACKEND_DJANGO:
            from aiida.orm.implementation.django.computer import Util as ComputerUtil
            return Util(ComputerUtil())
        elif settings.BACKEND == BACKEND_SQLA:
            from aiida.orm.implementation.sqlalchemy.computer import Util as ComputerUtil
            return Util(ComputerUtil())

    def delete_computer(self, pk):
        return self._backend.delete_computer(pk)


def delete_computer(computer=None, pk=None):
    if computer is not None:
        if not isinstance(computer, Computer):
            raise TypeError("computer must be an instance of "
                            "aiida.orm.computer.Computer")
        if pk is not None:
            assert computer.pk == pk, "Computer and pk do not match"
        else:
            pk = computer.pk

    if pk is not None:
        Util.get_default().delete_computer(pk)
    else:
        raise ValueError("Supply a valid computer or pk")
