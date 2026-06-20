import random
import uuid
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from .models import Booking, Payment



