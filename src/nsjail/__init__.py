from ._nsjail_version import __nsjail_version__
from .locator import *
from .options import *
from .process import *
from .version import __version__, __version_tuple__

# Programmatic namespace entry (Python 3.12+)
try:
    from .context import NamespaceContext
except ImportError:
    NamespaceContext = None  # type: ignore[misc, assignment]
