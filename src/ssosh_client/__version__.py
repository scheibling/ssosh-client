"""Module information."""
import os

# The title and description of the package
__title__ = "ssosh-client"
__description__ = """
    A python-based cli client for SSO Shell
"""

# The version and build number
# Without specifying a unique number, you cannot overwrite packages in the PyPi repo
__version__ = os.getenv("RELEASE_NAME", "0.1-dev" + os.getenv("GITHUB_RUN_ID", ""))

# Author and license information
__author__ = "Lars Scheibling"
__author_email__ = "lars@scheibling.se"
__license__ = "GnuPG 3.0"

# URL to the project
__url__ = f"https://github.com/scheiblingco/{__title__}"
