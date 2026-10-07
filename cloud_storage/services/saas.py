"""
Cloud Storage - SaaS (Support as a Service) - entry point. Feature code lives in ./saas/.
"""

import os

# ./saas/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_storage.services.saas.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "saas")]

from cloud_storage.services.saas.service import *  # noqa: F401,F403
