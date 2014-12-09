# coding=utf-8

from collections import OrderedDict

import pandas as pd
import numpy as np
import h5py

def aggregate_columns(dataframe, columns_dict):
    
    aggr_data = OrderedDict()
    def get_term(source_col):
        if isinstance(source_col, dict):
            return dataframe[source_col['name']] * source_col['coeff']
        else:
            return dataframe[source_col]

    for new_column in columns_dict:
        if isinstance(new_column, dict):
            source_cols = new_column['source_cols']
            aggr_data[new_column['name']] = sum(map(get_term, source_cols))
        else:
            aggr_data[new_column] = dataframe[new_column]

    aggr_dataframe = pd.DataFrame(
        aggr_data, index=dataframe.index, columns=aggr_data.keys())

    return aggr_dataframe


def load(thing):
    if type(thing) is h5py.Group:
        return thing

    elif type(thing) is h5py.Dataset:
        dataset = thing
        try:
            datatype = dataset.attrs['datatype']
        except KeyError:
            raise KeyError("no datatype specified in " + str(dataset))
    else:
        raise ValueError('Cannot load', str(thing))
    
    if str(pd.Series) == datatype:
        return pd.Series(
            index=dataset['index'][:],
            data=dataset['value'][:])
    else:
        try:
            return dataset[()]
        except:
            raise RuntimeError("could not load type '" + str(T) + '"')


def load_dict(hdf5_group, required, optional=None):
    names = required
    
    if optional is not None:
        names += tuple([n for n in optional if n in hdf5_group])

    return {name : load(hdf5_group[name]) for name in names}


def save(data, name, hdf5_group):
    if data is None:
        return

    if type(data) is dict:
        subgroup = hdf5_group.require_group(name)
        save_dict(data, subgroup)

    datatype_name = str(type(data))

    if type(data) is str:
        data = unicode(data)

    if type(data) is pd.Series:
        if len(data) is 0:
            return
            
        data = structured_array({
            'index' : data.index.values,
            'value' : data.values})

    if type(data) is unicode:
        ds = hdf5_group.create_dataset(
            name,
            data=data,
            dtype=h5py.special_dtype(vlen=unicode))
    else:
        try:
            ds = hdf5_group.create_dataset(name, data=data)
        except TypeError:
            raise TypeError(
                'cannot save ' + str(type(data)) + ' : ' + str(data))

    ds.attrs['datatype'] = datatype_name
    return ds

def save_dict(data_dict, hdf5_group):
    for key in data_dict:
        item = data_dict[key]
        if type(item) is dict:
            subgroup = hdf5_group.require_group(key)
            subgroup.attrs['name'] = key
            save_dict(item, subgroup)
        else:
            data = item
            dataset_name = key
            save(data, dataset_name, hdf5_group)

def structured_array(d):
    for key in d:
        if type(d) is not np.ndarray:
            d[key] = np.array(d[key])
            
    dtype = np.dtype([(key, d[key].dtype) for key in d])    
    return np.array(zip(*d.values()), dtype=dtype)