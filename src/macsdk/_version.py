"""Version and project information for MACSDK.

The version is read dynamically from package metadata (pyproject.toml).
This ensures that `uv version --bump` commands automatically propagate
to the runtime version without manual synchronization.

Note: This module is intentionally minimal to allow fast imports
in the CLI without loading heavy dependencies.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("macsdk")
except PackageNotFoundError:
    # Package not installed (development mode without editable install)
    __version__ = "0.0.0.dev0"

__author__ = "Juanje Ojeda"
__email__ = "juanje@redhat.com"

# Project URLs
__repo_url__ = "https://github.com/juanje/macsdk"
__docs_url__ = "https://github.com/juanje/macsdk#readme"
