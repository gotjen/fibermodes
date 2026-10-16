"""Shared pytest configuration for the fibermodes test suite."""

# Legacy helper modules that are not part of the active test suite.
# Their names do not match ``test_*.py``, but list them explicitly so that a
# broader ``python_files`` setting never collects them:
#
# - ``fiber/solver/cuda.py`` imports ``tests.fiber.solver.tlsif`` and
#   ``fibermodes.fiber.solver.cuda``; neither module exists any more, and the
#   class was already marked "Implementation not finished".
# - ``simulator/psimulator.py`` imports ``tests.simulator.simulator``, which no
#   longer exists (it became ``test_simulator.py``).
collect_ignore = [
    "fiber/solver/cuda.py",
    "simulator/psimulator.py",
]
