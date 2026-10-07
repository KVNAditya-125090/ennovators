"""
Cloud Storage - Customer - entry point. Feature code lives in ./customer/.
"""

import os

# ./customer/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_storage.users.customer.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "customer")]

from cloud_storage.users.customer.service import *  # noqa: F401,F403
