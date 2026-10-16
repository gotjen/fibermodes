"""Tests for fibermodes.simulator.psimulator.PSimulator."""

import os.path
import threading

from fibermodes import HE11
from fibermodes.simulator import PSimulator, Simulator
from fibermodes.simulator import psimulator

SMF28 = os.path.join(os.path.dirname(__file__), os.pardir, "fiber",
                     "smf28.fiber")


def test_does_not_fork_the_calling_process():
    """Fork in a multi-threaded process (Qt GUI) can deadlock. Pool
    workers are started with forkserver or spawn instead."""
    assert psimulator.MP_CONTEXT.get_start_method() in ("forkserver",
                                                        "spawn")


def test_same_results_as_simulator():
    psim = PSimulator(SMF28, [1310e-9, 1550e-9], processes=2)
    sim = Simulator(SMF28, [1310e-9, 1550e-9])
    assert list(psim.modes()) == list(sim.modes())
    assert list(psim.neff()) == list(sim.neff())


def test_from_a_thread(recwarn):
    """As in the GUI: the pool is made from a non-main thread. Python
    3.12+ warns when it forks a multi-threaded process (deadlock risk)."""
    result = {}

    def run():
        psim = PSimulator(SMF28, 1550e-9, processes=2)
        result["neff"] = list(psim.neff())

    t = threading.Thread(target=run)
    t.start()
    t.join(120)
    assert HE11 in result["neff"][0][0]
    forks = [w for w in recwarn if "fork" in str(w.message)]
    assert forks == []
