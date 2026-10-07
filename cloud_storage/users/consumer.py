"""
Cloud Storage - Consumer - entry point. Feature code lives in ./consumer/.
"""

import os

# ./consumer/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_storage.users.consumer.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "consumer")]

from cloud_storage.users.consumer.service import *  # noqa: F401,F403
