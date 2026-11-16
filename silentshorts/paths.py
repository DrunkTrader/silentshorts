"""Repository-root paths.

The modules live in the package, but fonts/, assets/, split_library/ and the
cookie files stay at the repository root, so lookups that used to be relative
to a module's own directory go through PROJECT_ROOT.
"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
