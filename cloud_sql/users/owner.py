"""
Cloud SQL - Owner - entry point. Feature code lives in ./owner/.
"""

import os

# ./owner/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_sql.users.owner.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "owner")]

from cloud_sql.users.owner.service import *  # noqa: F401,F403
