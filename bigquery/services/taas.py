"""
BigQuery - TaaS (Transport as a Service) - entry point. Feature code lives in ./taas/.
"""

import os

# ./taas/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, bigquery.services.taas.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "taas")]

from bigquery.services.taas.service import *  # noqa: F401,F403
