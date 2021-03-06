from __future__ import absolute_import

import pytest

from subprocess import check_call
from mpi4py import MPI

import numpy as np

from sympy import cos, Symbol  # noqa

from devito import (Grid, TimeDimension, SteppingDimension, SpaceDimension, # noqa
                    Constant, Function, TimeFunction, Eq, configuration, SparseFunction, # noqa
                    SparseTimeFunction)  # noqa
from devito.types import Scalar, Array
from devito.ir.iet import Iteration
from devito.tools import as_tuple


skipif_yask = pytest.mark.skipif(configuration['backend'] == 'yask',
                                 reason="YASK testing is currently restricted")


# Testing dimensions for space and time
grid = Grid(shape=(3, 3, 3))
time = grid.time_dim
t = grid.stepping_dim
x, y, z = grid.dimensions


def scalar(name):
    return Scalar(name=name)


def array(name, shape, dimensions, onstack=False):
    return Array(name=name, shape=shape, dimensions=dimensions,
                 onstack=onstack, onheap=(not onstack))


def constant(name):
    return Constant(name=name)


def function(name, shape, dimensions):
    return Function(name=name, shape=shape, dimensions=dimensions)


def timefunction(name, space_order=1):
    return TimeFunction(name=name, grid=grid, space_order=space_order)


@pytest.fixture(scope="session")
def unit_box(name='a', shape=(11, 11)):
    """Create a field with value 0. to 1. in each dimension"""
    grid = Grid(shape=shape)
    a = Function(name=name, grid=grid)
    dims = tuple([np.linspace(0., 1., d) for d in shape])
    a.data[:] = np.meshgrid(*dims)[1]
    return a


@pytest.fixture(scope="session")
def unit_box_time(name='a', shape=(11, 11)):
    """Create a field with value 0. to 1. in each dimension"""
    grid = Grid(shape=shape)
    a = TimeFunction(name=name, grid=grid, time_order=1)
    dims = tuple([np.linspace(0., 1., d) for d in shape])
    a.data[0, :] = np.meshgrid(*dims)[1]
    a.data[1, :] = np.meshgrid(*dims)[1]
    return a


@pytest.fixture(scope="session")
def points(grid, ranges, npoints, name='points'):
    """Create a set of sparse points from a set of coordinate
    ranges for each spatial dimension.
    """
    points = SparseFunction(name=name, grid=grid, npoint=npoints)
    for i, r in enumerate(ranges):
        points.coordinates.data[:, i] = np.linspace(r[0], r[1], npoints)
    return points


@pytest.fixture(scope="session")
def time_points(grid, ranges, npoints, name='points', nt=10):
    """Create a set of sparse points from a set of coordinate
    ranges for each spatial dimension.
    """
    points = SparseTimeFunction(name=name, grid=grid, npoint=npoints, nt=nt)
    for i, r in enumerate(ranges):
        points.coordinates.data[:, i] = np.linspace(r[0], r[1], npoints)
    return points


@pytest.fixture(scope="session")
def dims():
    return {'i': SpaceDimension(name='i'),
            'j': SpaceDimension(name='j'),
            'k': SpaceDimension(name='k'),
            'l': SpaceDimension(name='l'),
            's': SpaceDimension(name='s'),
            'q': SpaceDimension(name='q')}


@pytest.fixture(scope="session")
def iters(dims):
    return [lambda ex: Iteration(ex, dims['i'], (0, 3, 1)),
            lambda ex: Iteration(ex, dims['j'], (0, 5, 1)),
            lambda ex: Iteration(ex, dims['k'], (0, 7, 1)),
            lambda ex: Iteration(ex, dims['s'], (0, 4, 1)),
            lambda ex: Iteration(ex, dims['q'], (0, 4, 1)),
            lambda ex: Iteration(ex, dims['l'], (0, 6, 1)),
            lambda ex: Iteration(ex, x, (0, 5, 1)),
            lambda ex: Iteration(ex, y, (0, 7, 1)),
            lambda ex: Iteration(ex, z, (0, 7, 1))]


@pytest.fixture(scope="session", autouse=True)
def t0(dims):
    return scalar('t0').indexify()


@pytest.fixture(scope="session", autouse=True)
def t1(dims):
    return scalar('t1').indexify()


@pytest.fixture(scope="session", autouse=True)
def t2(dims):
    return scalar('t2').indexify()


@pytest.fixture(scope="session", autouse=True)
def t3(dims):
    return scalar('t3').indexify()


@pytest.fixture(scope="session", autouse=True)
def a(dims):
    return array('a', (3,), (dims['i'],)).indexify()


@pytest.fixture(scope="session", autouse=True)
def a_dense(dims):
    return function('a_dense', (3,), (dims['i'],)).indexify()


@pytest.fixture(scope="session", autouse=True)
def const():
    return constant('constant').indexify()


@pytest.fixture(scope="session", autouse=True)
def b(dims):
    return array('b', (3,), (dims['i'],)).indexify()


@pytest.fixture(scope="session", autouse=True)
def b_dense(dims):
    return function('b_dense', (3,), (dims['i'],)).indexify()


@pytest.fixture(scope="session", autouse=True)
def c(dims):
    return array('c', (3, 5), (dims['i'], dims['j'])).indexify()


@pytest.fixture(scope="session", autouse=True)
def c_stack(dims):
    return array('c_stack', (3, 5), (dims['i'], dims['j']), True).indexify()


@pytest.fixture(scope="session", autouse=True)
def d(dims):
    return array('d', (3, 5, 7), (dims['i'], dims['j'], dims['k'])).indexify()


@pytest.fixture(scope="session", autouse=True)
def e(dims):
    dimensions = [dims['k'], dims['s'], dims['q'], dims['i'], dims['j']]
    return array('e', (7, 4, 4, 3, 5), dimensions).indexify()


@pytest.fixture(scope="session", autouse=True)
def ti0(dims):
    return array('ti0', (3, 5, 7), (x, y, z)).indexify()


@pytest.fixture(scope="session", autouse=True)
def ti1(dims):
    return array('ti1', (3, 5, 7), (x, y, z)).indexify()


@pytest.fixture(scope="session", autouse=True)
def ti2(dims):
    return array('ti2', (3, 5), (x, y)).indexify()


@pytest.fixture(scope="session", autouse=True)
def ti3(dims):
    return array('ti3', (3, 5, 7), (x, y, z)).indexify()


@pytest.fixture(scope="session", autouse=True)
def tu(dims):
    return timefunction('tu', space_order=4).indexify()


@pytest.fixture(scope="session", autouse=True)
def tv(dims):
    return timefunction('tv', space_order=4).indexify()


@pytest.fixture(scope="session", autouse=True)
def tw(dims):
    return timefunction('tw', space_order=4).indexify()


@pytest.fixture(scope="session", autouse=True)
def fa(dims):
    return array('fa', (3,), (x,)).indexed


@pytest.fixture(scope="session", autouse=True)
def fb(dims):
    return array('fb', (3,), (x,)).indexed


@pytest.fixture(scope="session", autouse=True)
def fc(dims):
    return array('fc', (3, 5), (x, y)).indexed


@pytest.fixture(scope="session", autouse=True)
def fd(dims):
    return array('fd', (3, 5), (x, y)).indexed


@pytest.fixture(scope="session", autouse=True)
def fe(dims):
    return array('fe', (3, 5, 3), (x, y, z)).indexed


def EVAL(exprs, *args):
    """
    Convert strings into SymPy objects.

    Required to work around this 'won't fix' Python3 issue: ::

        http://stackoverflow.com/questions/29336616/eval-scope-in-python-2-vs-3
    """
    # Cannot use list comprehension because of the issue linked in the docstring
    scope = {}
    for i in args:
        try:
            scope[i.base.function.name] = i
            for j in i.base.function.indices:
                scope[j.name] = j
        except AttributeError:
            scope[i.label.name] = i
            for j in i.function.indices:
                scope[j.name] = j
    processed = []
    for i in as_tuple(exprs):
        processed.append(eval(i, globals(), scope))
    return processed[0] if isinstance(exprs, str) else processed


def configuration_override(key, value):
    def dec(f):
        def wrapper(*args, **kwargs):
            oldvalue = configuration[key]
            configuration[key] = value
            f(*args, **kwargs)
            configuration[key] = oldvalue

        return wrapper

    return dec


# Support to run MPI tests
# This is partly extracted from:
# `https://github.com/firedrakeproject/firedrake/blob/master/tests/conftest.py`

def parallel(item):
    """Run a test in parallel.

    :parameter item: The test item to run.
    """
    marker = item.get_marker("parallel")
    nprocs = as_tuple(marker.kwargs.get("nprocs", 2))
    for i in nprocs:
        if i < 2:
            raise RuntimeError("Need at least two processes to run parallel test")

        # Only spew tracebacks on rank 0.
        # Run xfailing tests to ensure that errors are reported to calling process
        call = ["mpiexec", "-n", "1", "python", "-m", "pytest", "--runxfail", "-s",
                "-q", "%s::%s" % (item.fspath, item.name)]
        call.extend([":", "-n", "%d" % (i - 1), "python", "-m", "pytest",
                     "--runxfail", "--tb=no", "-q", "%s::%s" % (item.fspath, item.name)])
        check_call(call)


def pytest_configure(config):
    """Register an additional marker."""
    config.addinivalue_line(
        "markers",
        "parallel(nprocs): mark test to run in parallel on nprocs processors")


def pytest_runtest_setup(item):
    if item.get_marker("parallel") and MPI.COMM_WORLD.size == 1:
        # Blow away function arg in "master" process, to ensure
        # this test isn't run on only one process.
        item.obj = lambda *args, **kwargs: True


def pytest_runtest_call(item):
    if item.get_marker("parallel") and MPI.COMM_WORLD.size == 1:
        # Spawn parallel processes to run test
        parallel(item)
