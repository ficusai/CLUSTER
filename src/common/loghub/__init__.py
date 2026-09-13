"""loghub package — re-exports from loghub.py for backward compatibility."""
import importlib.util
import os as _os

_pkg_dir = _os.path.dirname(__file__)
_mod_path = _os.path.join(_pkg_dir, "..", "loghub.py")
_mod_path = _os.path.abspath(_mod_path)

_spec = importlib.util.spec_from_file_location("common._loghub_impl", _mod_path, submodule_search_locations=[])
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

LogHub = _mod.LogHub
LogWriter = _mod.LogWriter
