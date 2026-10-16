"""
Product as a Service (PaaS) Router - entry point. Feature code lives in ./paas/.
"""

import os

# ./paas/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_run.services.paas.router could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "paas")]

from cloud_run.services.paas.router import *  # noqa: F401,F403
