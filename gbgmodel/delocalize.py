import sys
import os.path
from collections import defaultdict
import pandas as pd
import numpy as np
import pandas.tseries.offsets as offsets

SEPARATOR = ';'
DEFAULT_SRC_TIMEZONE = 'Europe/Stockholm'

def read_and_convert(path_in, path_out, src_timezone=DEFAULT_SRC_TIMEZONE):
    data = pd.read_csv(path_in, index_col=0, sep=SEPARATOR, encoding='utf-8', parse_dates=True)
    data = data.tz_localize(tz=src_timezone, axis='rows', ambiguous='infer')
    data = data.tz_convert(tz='UTC', axis='rows')
    data.to_csv(path_out, sep=SEPARATOR)

if __name__ == '__main__':
    read_and_convert(*sys.argv[1:])