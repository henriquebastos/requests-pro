from datetime import datetime
from functools import partial
from zoneinfo import ZoneInfo


UTC = ZoneInfo("UTC")
utc_now = partial(datetime.now, UTC)
