"""Graphical user interfaces for fibermodes.

The Qt binding is selected through qtpy. PyQt6 is the default; set the
``QT_API`` environment variable to select another binding. qtpy is imported
here, before pyqtgraph, so that both use the same binding.

"""

import os

os.environ.setdefault("QT_API", "pyqt6")

import qtpy  # noqa: E402,F401


class blockSignals(object):

    """Allow to use with statement to block signals.

    with object.blockSignals:
        object.do_stuff()

    """

    def __init__(self, obj):
        self.obj = obj

    def __enter__(self):
        self._status = self.obj.blockSignals(True)
        return self.obj

    def __exit__(self, *args, **kwargs):
        self.obj.blockSignals(self._status)
