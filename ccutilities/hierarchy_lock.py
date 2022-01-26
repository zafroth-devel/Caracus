from ccutilities.arangodb_utils import hierarchy
from ccmaintainp.models import HinyangoHierarchyLock
from django.core.exceptions import ObjectDoesNotExist,MultipleObjectsReturned
from ccaccounts.models import AccountProfile
import json
import itertools
from datetime import datetime
from ccutilities.utilities import residenttenant