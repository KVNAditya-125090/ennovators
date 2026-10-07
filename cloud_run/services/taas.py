"""
Transport as a Service (TaaS) Router - entry point. Feature code lives in ./taas/.
"""

import os

# ./taas/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_run.services.taas.router could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "taas")]

from cloud_run.services.taas.router import *  # noqa: F401,F403
