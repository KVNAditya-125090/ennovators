"""
BigQuery - Customer - entry point. Feature code lives in ./customer/.
"""

import os

# ./customer/ has the same name as this module and no __init__.py, so register it as this
# module's package path. Without this, bigquery.users.customer.service could not be imported.
__path__ = [os.path.join(os.path.dirname(__file__), "customer")]

from bigquery.users.customer.service import *  # noqa: F401,F403
