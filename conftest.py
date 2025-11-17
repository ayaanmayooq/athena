# conftest.py
import os
import sys

# Absolute path to the repo root (/.../athena-v1)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure the repo root is on sys.path *before* tests/
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
