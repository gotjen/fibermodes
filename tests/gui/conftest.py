"""Shared configuration for the GUI smoke tests (pytest-qt)."""

import os

# Use the offscreen platform when no display is available. pytest-qt makes
# the QApplication lazily, so this setting is in place before Qt starts.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
