"""
Timezone utilities for Philippine timezone support
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# Philippines timezone (UTC+8, no DST)
PH_TZ = ZoneInfo('Asia/Manila')

def get_ph_datetime():
    """Get current datetime in Philippine timezone"""
    return datetime.now(PH_TZ)

def get_ph_datetime_str():
    """Get current datetime as string in Philippine timezone (ISO format)"""
    return get_ph_datetime().isoformat()

def localize_to_ph(dt):
    """Convert datetime to Philippine timezone"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = dt.replace(tzinfo=ZoneInfo('UTC'))
    return dt.astimezone(PH_TZ)

def format_ph_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """Format datetime in Philippine timezone"""
    if dt is None:
        return None
    ph_dt = localize_to_ph(dt) if dt.tzinfo else dt.replace(tzinfo=PH_TZ)
    return ph_dt.strftime(format_str)
