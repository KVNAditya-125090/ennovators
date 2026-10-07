"""
Owner Router - operates all four services (MaaS, PaaS, TaaS, SaaS). - entry point. Feature code lives in ./owner/.
"""

import os

# ./owner/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_run.users.owner.router could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "owner")]

from cloud_run.users.owner.router import *  # noqa: F401,F403
