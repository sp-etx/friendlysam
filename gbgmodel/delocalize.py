import sys
import os.path
from collections import defaultdict
import pandas as pd
import numpy as np
import pandas.tseries.offsets as offsets

SEPARATOR = ';'
SRC_TIMEZONE = 'Europe/Stockholm'

def start_dst(year):
    # Daylight saving time starts at 03:00 on the last Sunday in March.
    return pd.datetime(year, 3, 1) + offsets.LastWeekOfMonth(weekday=6) + offsets.Hour(3)

def start_nt(year):
    # Normal time starts at 03:00 on the last Sunday in October.
    return pd.datetime(year, 10, 1) + offsets.LastWeekOfMonth(weekday=6) + offsets.Hour(3)

def never_happens(time):
    # 02:00-03:00 on the last Sunday in March. (Never happens.)
    end = start_dst(time.year)
    start = end - offsets.Hour(1)
    return start <= time < end

def is_ambiguous(time):
    # 02:00-03:00 on the last Sunday in October. (Happens twice.)
    end = start_nt(time.year)
    start = end - offsets.Hour(1)
    return start <= time < end

def read_and_convert(path_in, path_out):
    data = pd.read_csv(path_in, index_col=0, sep=SEPARATOR, encoding='utf-8', parse_dates=True)
    assert isinstance(data, pd.DataFrame)

    for time in data.index[[never_happens(t) for t in data.index]]:
        assert data.loc[time].isnull().all()
        data.drop(time, axis='rows', inplace=True)
    
    reentered_ambiguous = defaultdict(lambda: False)
    is_dst = []
    previous_time = None
    for time in data.index:
        assert not never_happens(time)

        # This is a simple guess for what's DST and not
        this_is_dst = start_dst(time.year) <= time < start_nt(time.year)
        
        # But if we have just gone "back" in time
        if previous_time is not None and time <= previous_time:
            # We should be in the ambiguous hour, and then we are actually NOT in DST
            assert is_ambiguous(time) and not reentered_ambiguous[time.year]
            reentered_ambiguous[time.year] = True
            this_is_dst = False

        is_dst.append(this_is_dst)
        previous_time = time

    data = data.tz_localize(tz=SRC_TIMEZONE, axis='rows', ambiguous=np.array(is_dst))
    data = data.tz_convert(tz='UTC', axis='rows')
    data['dst'] = is_dst
    data.to_csv(path_out, sep=SEPARATOR)
    print(data)

if __name__ == '__main__':
    read_and_convert(*sys.argv[1:])