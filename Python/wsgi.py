"""
WSGI entry point for Gunicorn.
Loads the Flask app from project-template.py which has a hyphen in the filename.
"""
import os
import sys
from importlib.machinery import SourceFileLoader

BASE_DIR = os.path.dirname(__file__)
# Ensure the Python directory is importable (so `import user` etc. works)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
PT_PATH = os.path.join(BASE_DIR, 'project-template.py')

if not os.path.exists(PT_PATH):
    raise RuntimeError(f"project-template.py not found at {PT_PATH}")

mod = SourceFileLoader('project_template', PT_PATH).load_module()
app = getattr(mod, 'app', None)
if app is None:
    raise RuntimeError("Flask app not found in project-template.py (expected variable 'app')")
