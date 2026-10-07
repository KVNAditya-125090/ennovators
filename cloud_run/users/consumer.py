"""
Consumer Router - consumes the services (PaaS catalog, TaaS shipments, demand forecast). - entry point. Feature code lives in ./consumer/.
"""

import os

# ./consumer/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, cloud_run.users.consumer.router could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "consumer")]

from cloud_run.users.consumer.router import *  # noqa: F401,F403
