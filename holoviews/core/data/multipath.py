import numpy as np

from ..util import max_range
from .interface import Interface

class MultiInterface(Interface):
    """
    MultiInterface allows wrapping around a list of tabular datasets
    including dataframes, the columnar dictionary format or 2D tabular
    NumPy arrays. Using the split method the list of tabular data can
    be split into individual datasets.
    """

    types = ()

    datatype = 'multi'

    subtypes = ['dataframe', 'dictionary', 'array', 'dask']

    @classmethod
    def init(cls, eltype, data, kdims, vdims):
        new_data = []
        dims = {'kdims': eltype.kdims, 'vdims': eltype.vdims}
        extra_kws = {}
        for d in data:
            d, interface, dims, extra_kws = Interface.initialize(eltype, d, kdims, vdims,
                                                                 datatype=cls.subtypes)
            new_data.append(d)
        return new_data, dims, extra_kws

    @classmethod
    def validate(cls, dataset):
        pass

    @classmethod
    def template(cls, dataset):
        """
        Returns a Dataset template used as a wrapper around the data
        contained within the multi-interface dataset.
        """
        from . import Dataset
        vdims = dataset.vdims if getattr(dataset, 'level', None) is None else []
        return Dataset(dataset.data[0], datatype=cls.subtypes,
                       kdims=dataset.kdims, vdims=vdims)

    @classmethod
    def dimension_type(cls, dataset, dim):
        if not dataset.data:
            return float
        ds = cls.template(dataset)
        return ds.interface.dimension_type(ds, dim)

    @classmethod
    def range(cls, dataset, dim):
        if not dataset.data:
            return (None, None)
        ranges = []
        ds = cls.template(dataset)

        # Backward compatibility for level
        level = getattr(dataset, 'level', None)
        dim = dataset.get_dimension(dim)
        if level is not None and dim is dataset.vdims[0]:
            return (level, level)

        for d in dataset.data:
            ds.data = d
            ranges.append(ds.interface.range(ds, dim))
        return max_range(ranges)

    @classmethod
    def select(cls, dataset, selection_mask=None, **selection):
        ds = cls.template(dataset)
        data = []
        for d in dataset.data:
            ds.data = d
            sel = ds.interface.select(ds, **selection)
            data.append(sel)
        return data

    @classmethod
    def aggregate(cls, columns, dimensions, function, **kwargs):
        raise NotImplementedError

    @classmethod
    def groupby(cls, columns, dimensions, container_type, group_type, **kwargs):
        raise NotImplementedError

    @classmethod
    def sample(cls, columns, samples=[]):
        raise NotImplementedError

    @classmethod
    def shape(cls, dataset):
        if not dataset.data:
            return (0, len(dataset.dimensions()))

        rows, cols = 0, 0
        ds = cls.template(dataset)
        for d in dataset.data:
            ds.data = d
            r, cols = ds.interface.shape(ds)
            rows += r
        return rows+len(dataset.data)-1, cols

    @classmethod
    def length(cls, dataset):
        if not dataset.data:
            return 0
        length = 0
        ds = cls.template(dataset)
        for d in dataset.data:
            ds.data = d
            length += ds.interface.length(ds)
        return length+len(dataset.data)-1

    @classmethod
    def nonzero(cls, dataset):
        return bool(cls.length(dataset))

    @classmethod
    def redim(cls, dataset, dimensions):
        if not dataset.data:
            return dataset.data
        new_data = []
        ds = cls.template(dataset)
        for d in dataset.data:
            ds.data = d
            new_data.append(ds.interface.redim(ds, dimensions))
        return new_data

    @classmethod
    def values(cls, dataset, dimension, expanded, flat):
        if not dataset.data:
            return np.array([])
        values = []
        ds = cls.template(dataset)
        for d in dataset.data:
            ds.data = d
            values.append(ds.interface.values(ds, dimension, expanded, flat))
            if expanded:
                values.append([np.NaN])
        return np.concatenate(values[:-1] if expanded else values) if values else []

    @classmethod
    def split(cls, dataset, start, end):
        """
        Splits a multi-interface Dataset into regular Datasets using
        regular tabular interfaces.
        """
        from ...element.path import BaseShape
        if isinstance(dataset, BaseShape):
            return [dataset]
        objs = []
        for d in dataset.data[start: end]:
            objs.append(dataset.clone(d, datatype=cls.subtypes))
        return objs


Interface.register(MultiInterface)