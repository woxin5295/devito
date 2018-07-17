from collections import OrderedDict

from devito.core.autotuning import autotune
from devito.cgen_utils import printmark
from devito.ir.iet import (List, Transformer, FindNodes, HaloSpot, Call, MetaCall,
                           filter_iterations, retrieve_iteration_tree)
from devito.ir.support import align_accesses
from devito.parameters import configuration
from devito.mpi import copy, sendrecv, update_halo
from devito.operator import OperatorRunnable
from devito.tools import flatten

__all__ = ['Operator']


class OperatorCore(OperatorRunnable):

    def _specialize_exprs(self, expressions):
        # Align data accesses to the computational domain
        key = lambda i: i.is_TensorFunction
        expressions = [align_accesses(e, key=key) for e in expressions]
        return super(OperatorCore, self)._specialize_exprs(expressions)

    def _generate_mpi(self, iet, **kwargs):
        if configuration['mpi'] is False:
            return iet

        # For each function, generate all necessary C-level routines to perform
        # a halo exchange
        calls = []
        callables = []
        cstructs = set()
        halo_spots = FindNodes(HaloSpot).visit(iet)
        for hs in halo_spots:
            for f, v in hs.halo_updates.items():
                callables.extend([copy(f, hs.fixed), copy(f, hs.fixed, True)])
                callables.append(sendrecv(f, hs.fixed))
                callables.append(update_halo(f, hs.fixed))

                stencil = [1]*len(v)  # FIXME
                fixed = list(hs.fixed.values())  # FIXME
                comm = f.grid.distributor._C_comm
                nb = f.grid.distributor._C_neighbours.obj
                dsizes = [d.symbolic_size for d in f.dimensions]
                parameters = [f] + stencil + [comm, nb] + fixed + dsizes
                calls.append(Call('update_halo_%s' % f.name, parameters))
                from IPython import embed; embed()

                cstructs.add(f.grid.distributor._C_neighbours.cdef)

        self._func_table.update(OrderedDict([(i.name, MetaCall(i, True))
                                             for i in callables]))

        # Sorting is for deterministic code generation. However, in practice,
        # we don't expect `cstructs` to contain more than one element because
        # there should always be one grid per Operator (though we're not really
        # enforcing this)
        self._globals.extend(sorted(cstructs, key=lambda i: i.tpname))

        self._includes.append('mpi.h')

        return iet

    def _autotune(self, args):
        if self._dle_flags.get('blocking', False):
            return autotune(self, args, self.parameters, self._dle_args)
        else:
            return args


class OperatorDebug(OperatorCore):
    """
    Decorate the generated code with useful print statements.
    """

    def __init__(self, expressions, **kwargs):
        super(OperatorDebug, self).__init__(expressions, **kwargs)
        self._includes.append('stdio.h')

        # Minimize the trip count of the sequential loops
        iterations = set(flatten(retrieve_iteration_tree(self.body)))
        mapper = {i: i._rebuild(limits=(max(i.offsets) + 2))
                  for i in iterations if i.is_Sequential}
        self.body = Transformer(mapper).visit(self.body)

        # Mark entry/exit points of each non-sequential Iteration tree in the body
        iterations = [filter_iterations(i, lambda i: not i.is_Sequential, 'any')
                      for i in retrieve_iteration_tree(self.body)]
        iterations = [i[0] for i in iterations if i]
        mapper = {t: List(header=printmark('In nest %d' % i), body=t)
                  for i, t in enumerate(iterations)}
        self.body = Transformer(mapper).visit(self.body)


class Operator(object):

    def __new__(cls, *args, **kwargs):
        cls = OperatorDebug if kwargs.pop('debug', False) else OperatorCore
        obj = cls.__new__(cls, *args, **kwargs)
        obj.__init__(*args, **kwargs)
        return obj
