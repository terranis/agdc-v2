# coding=utf-8
"""
Module
"""
from __future__ import absolute_import

import copy
import csv
import datetime
import io
import uuid
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
import yaml
from click.testing import CliRunner
from dateutil import tz
from psycopg2._range import NumericRange

import datacube.scripts.cli_app
import datacube.scripts.search_tool
from datacube.index._api import Index
from datacube.index.postgres import PostgresDb
from datacube.model import Dataset
from datacube.model import DatasetType
from datacube.model import Range
from datacube.scripts import dataset as dataset_script

try:
    from typing import List
except ImportError:
    pass

_EXAMPLE_LS7_NBAR_DATASET_FILE = Path(__file__).parent.joinpath('ls7-nbar-example.yaml')


@pytest.fixture
def pseudo_ls8_type(index, default_metadata_type):
    index.products.add_document({
        'name': 'ls8_telemetry',
        'description': 'telemetry test',
        'metadata': {
            'product_type': 'pseudo_ls8_data',
            'platform': {
                'code': 'LANDSAT_8'
            },
            'instrument': {
                'name': 'OLI_TIRS'
            },
            'format': {
                'name': 'PSEUDOMD'
            }
        },
        # We're actually using 'eo' because we do lat/lon searches below...
        'metadata_type': default_metadata_type.name
    })
    return index.products.get_by_name('ls8_telemetry')


@pytest.fixture
def pseudo_ls8_dataset(index, db, pseudo_ls8_type):
    id_ = str(uuid.uuid4())
    with db.connect() as connection:
        was_inserted = connection.insert_dataset(
            {
                'id': id_,
                'product_type': 'pseudo_ls8_data',
                'checksum_path': 'package.sha1',
                'ga_label': 'LS8_OLITIRS_STD-MD_P00_LC81160740742015089ASA00_'
                            '116_074_20150330T022553Z20150330T022657',

                'ga_level': 'P00',
                'size_bytes': 637660782,
                'platform': {
                    'code': 'LANDSAT_8'
                },
                # We're unlikely to have extent info for a raw dataset, we'll use it for search tests.
                'extent': {
                    'from_dt': datetime.datetime(2014, 7, 26, 23, 48, 0, 343853),
                    'to_dt': datetime.datetime(2014, 7, 26, 23, 52, 0, 343853),
                    'coord': {
                        'll': {'lat': -31.33333, 'lon': 149.78434},
                        'lr': {'lat': -31.37116, 'lon': 152.20094},
                        'ul': {'lat': -29.23394, 'lon': 149.85216},
                        'ur': {'lat': -29.26873, 'lon': 152.21782}
                    }
                },
                'image': {
                    'satellite_ref_point_start': {'x': 116, 'y': 74},
                    'satellite_ref_point_end': {'x': 116, 'y': 84},
                },
                'creation_dt': datetime.datetime(2015, 4, 22, 6, 32, 4),
                'instrument': {'name': 'OLI_TIRS'},
                'format': {
                    'name': 'PSEUDOMD'
                },
                'lineage': {
                    'source_datasets': {}
                }
            },
            id_,
            pseudo_ls8_type.id
        )
    assert was_inserted
    d = index.datasets.get(id_)
    # The dataset should have been matched to the telemetry type.
    assert d.type.id == pseudo_ls8_type.id

    return d


@pytest.fixture
def pseudo_ls8_dataset2(index, db, pseudo_ls8_type):
    # Like the previous dataset, but a day later in time.
    id_ = str(uuid.uuid4())
    with db.connect() as connection:
        was_inserted = connection.insert_dataset(
            {
                'id': id_,
                'product_type': 'pseudo_ls8_data',
                'checksum_path': 'package.sha1',
                'ga_label': 'LS8_OLITIRS_STD-MD_P00_LC81160740742015089ASA00_'
                            '116_074_20150330T022553Z20150330T022657',

                'ga_level': 'P00',
                'size_bytes': 637660782,
                'platform': {
                    'code': 'LANDSAT_8'
                },
                'image': {
                    'satellite_ref_point_start': {'x': 116, 'y': 74},
                    'satellite_ref_point_end': {'x': 116, 'y': 84},
                },
                # We're unlikely to have extent info for a raw dataset, we'll use it for search tests.
                'extent': {
                    'from_dt': datetime.datetime(2014, 7, 27, 23, 48, 0, 343853),
                    'to_dt': datetime.datetime(2014, 7, 27, 23, 52, 0, 343853),
                    'coord': {
                        'll': {'lat': -31.33333, 'lon': 149.78434},
                        'lr': {'lat': -31.37116, 'lon': 152.20094},
                        'ul': {'lat': -29.23394, 'lon': 149.85216},
                        'ur': {'lat': -29.26873, 'lon': 152.21782}
                    }
                },
                'creation_dt': datetime.datetime(2015, 4, 22, 6, 32, 4),
                'instrument': {'name': 'OLI_TIRS'},
                'format': {
                    'name': 'PSEUDOMD'
                },
                'lineage': {
                    'source_datasets': {}
                }
            },
            id_,
            pseudo_ls8_type.id
        )
    assert was_inserted
    d = index.datasets.get(id_)
    # The dataset should have been matched to the telemetry type.
    assert d.type.id == pseudo_ls8_type.id

    return d


# Datasets 3 and 4 mirror 1 and 2 but have a different path/row.
@pytest.fixture
def pseudo_ls8_dataset3(index, db, pseudo_ls8_type, pseudo_ls8_dataset):
    # type: (Index, PostgresDb, DatasetType, Dataset) -> Dataset

    # Same as 1, but a different path/row
    id_ = str(uuid.uuid4())
    dataset_doc = copy.deepcopy(pseudo_ls8_dataset.metadata_doc)
    dataset_doc['id'] = id_
    dataset_doc['image'] = {
        'satellite_ref_point_start': {'x': 116, 'y': 85},
        'satellite_ref_point_end': {'x': 116, 'y': 87},
    }

    with db.connect() as connection:
        was_inserted = connection.insert_dataset(
            dataset_doc,
            id_,
            pseudo_ls8_type.id
        )
    assert was_inserted
    d = index.datasets.get(id_)
    # The dataset should have been matched to the telemetry type.
    assert d.type.id == pseudo_ls8_type.id
    return d


@pytest.fixture
def pseudo_ls8_dataset4(index, db, pseudo_ls8_type, pseudo_ls8_dataset2):
    # type: (Index, PostgresDb, DatasetType, Dataset) -> Dataset

    # Same as 2, but a different path/row
    id_ = str(uuid.uuid4())
    dataset_doc = copy.deepcopy(pseudo_ls8_dataset2.metadata_doc)
    dataset_doc['id'] = id_
    dataset_doc['image'] = {
        'satellite_ref_point_start': {'x': 116, 'y': 85},
        'satellite_ref_point_end': {'x': 116, 'y': 87},
    }

    with db.connect() as connection:
        was_inserted = connection.insert_dataset(
            dataset_doc,
            id_,
            pseudo_ls8_type.id
        )
        assert was_inserted
        d = index.datasets.get(id_)
        # The dataset should have been matched to the telemetry type.
        assert d.type.id == pseudo_ls8_type.id
        return d


@pytest.fixture
def ls5_dataset_w_children(index, example_ls5_dataset_path, indexed_ls5_scene_dataset_types):
    # type: (Index, Path, DatasetType) -> Dataset
    # TODO: We need a higher-level API for indexing paths, rather than reaching inside the cli script
    datasets = list(
        dataset_script.load_datasets(
            [example_ls5_dataset_path],
            dataset_script.load_rules_from_types(index)
        )
    )
    assert len(datasets) == 1
    d = index.datasets.add(datasets[0])
    return index.datasets.get(d.id, include_sources=True)


@pytest.fixture
def ls5_dataset_nbar_type(ls5_dataset_w_children, indexed_ls5_scene_dataset_types):
    # type: (Dataset, List[DatasetType]) -> DatasetType
    for dataset_type in indexed_ls5_scene_dataset_types:
        if dataset_type.name == ls5_dataset_w_children.type.name:
            return dataset_type
    else:
        raise RuntimeError("LS5 type was not among types")


def test_search_dataset_equals(index, pseudo_ls8_dataset):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    datasets = index.datasets.search_eager(
        platform='LANDSAT_8'
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    datasets = index.datasets.search_eager(
        platform='LANDSAT_8',
        instrument='OLI_TIRS'
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # Wrong sensor name
    datasets = index.datasets.search_eager(
        platform='LANDSAT-8',
        instrument='TM',
    )
    assert len(datasets) == 0


def test_search_dataset_by_metadata(index, pseudo_ls8_dataset):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    datasets = index.datasets.search_by_metadata(
        {"platform": {"code": "LANDSAT_8"}, "instrument": {"name": "OLI_TIRS"}}
    )
    datasets = list(datasets)
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    datasets = index.datasets.search_by_metadata(
        {"platform": {"code": "LANDSAT_5"}, "instrument": {"name": "TM"}}
    )
    datasets = list(datasets)
    assert len(datasets) == 0


def test_search_day(index, pseudo_ls8_dataset):
    # type: (Index, Dataest) -> None

    # Matches day
    datasets = index.datasets.search_eager(
        time=datetime.date(2014, 7, 26)
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # Different day: no match
    datasets = index.datasets.search_eager(
        time=datetime.date(2014, 7, 27)
    )
    assert len(datasets) == 0


def test_search_dataset_ranges(index, pseudo_ls8_dataset):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """

    # In the lat bounds.
    datasets = index.datasets.search_eager(
        lat=Range(-30.5, -29.5),
        time=Range(
            datetime.datetime(2014, 7, 26, 23, 0, 0),
            datetime.datetime(2014, 7, 26, 23, 59, 0)
        )
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # Out of the lat bounds.
    datasets = index.datasets.search_eager(
        lat=Range(28, 32),
        time=Range(
            datetime.datetime(2014, 7, 26, 23, 48, 0),
            datetime.datetime(2014, 7, 26, 23, 50, 0)
        )
    )
    assert len(datasets) == 0

    # Out of the time bounds
    datasets = index.datasets.search_eager(
        lat=Range(-30.5, -29.5),
        time=Range(
            datetime.datetime(2014, 7, 26, 21, 48, 0),
            datetime.datetime(2014, 7, 26, 21, 50, 0)
        )
    )
    assert len(datasets) == 0

    # A dataset that overlaps but is not fully contained by the search bounds.
    # TODO: Do we want overlap as the default behaviour?
    # Should we distinguish between 'contains' and 'overlaps'?
    datasets = index.datasets.search_eager(
        lat=Range(-40, -30)
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # Single point search
    datasets = index.datasets.search_eager(
        lat=-30.0,
        time=Range(
            datetime.datetime(2014, 7, 26, 23, 0, 0),
            datetime.datetime(2014, 7, 26, 23, 59, 0)
        )
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    datasets = index.datasets.search_eager(
        lat=30.0,
        time=Range(
            datetime.datetime(2014, 7, 26, 23, 0, 0),
            datetime.datetime(2014, 7, 26, 23, 59, 0)
        )
    )
    assert len(datasets) == 0

    # Single timestamp search
    datasets = index.datasets.search_eager(
        lat=Range(-30.5, -29.5),
        time=datetime.datetime(2014, 7, 26, 23, 50, 0)
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    datasets = index.datasets.search_eager(
        lat=Range(-30.5, -29.5),
        time=datetime.datetime(2014, 7, 26, 23, 30, 0)
    )
    assert len(datasets) == 0


def test_search_globally(index, pseudo_ls8_dataset):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    # Insert dataset. It should be matched to the telemetry collection.
    # No expressions means get all.
    results = list(index.datasets.search())
    assert len(results) == 1

    # Dataset sources aren't loaded by default
    assert results[0].sources is None


def test_search_by_product(index, pseudo_ls8_type, pseudo_ls8_dataset, indexed_ls5_scene_dataset_types,
                           ls5_dataset_w_children):
    """
    :type index: datacube.index._api.Index
    """
    # Expect one product with our one dataset.
    products = list(index.datasets.search_by_product(
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert len(products) == 1
    product, datasets = products[0]
    assert product.id == pseudo_ls8_type.id
    assert next(datasets).id == pseudo_ls8_dataset.id


def test_search_or_expressions(index,
                               pseudo_ls8_type, pseudo_ls8_dataset,
                               ls5_dataset_nbar_type, ls5_dataset_w_children,
                               telemetry_metadata_type):
    # type: (Index, DatasetType, Dataset, DatasetType, Dataset) -> None

    # Four datasets:
    # Our standard LS8
    # - type=ls8_telemetry
    # LS5 with children:
    # - type=ls5_nbar_scene
    # - type=ls5_level1_scene
    # - type=ls5_satellite_telemetry_data

    all_datasets = index.datasets.search_eager()
    assert len(all_datasets) == 4
    all_ids = set(dataset.id for dataset in all_datasets)

    # OR all platforms: should return all datasets
    datasets = index.datasets.search_eager(
        platform=['LANDSAT_5', 'LANDSAT_7', 'LANDSAT_8']
    )
    assert len(datasets) == 4
    ids = set(dataset.id for dataset in datasets)
    assert ids == all_ids

    # OR expression with only one clause.
    datasets = index.datasets.search_eager(
        platform=['LANDSAT_8']
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # OR two products: return two
    datasets = index.datasets.search_eager(
        product=[pseudo_ls8_type.name, ls5_dataset_nbar_type.name]
    )
    assert len(datasets) == 2
    ids = set(dataset.id for dataset in datasets)
    assert ids == {pseudo_ls8_dataset.id, ls5_dataset_w_children.id}

    # eo OR telemetry: return all
    datasets = index.datasets.search_eager(
        metadata_type=[
            telemetry_metadata_type.name,
            pseudo_ls8_type.metadata_type.name
        ]
    )
    assert len(datasets) == 4
    ids = set(dataset.id for dataset in datasets)
    assert ids == all_ids

    # Redundant ORs should have no effect.
    datasets = index.datasets.search_eager(
        product=[pseudo_ls8_type.name, pseudo_ls8_type.name, pseudo_ls8_type.name]
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id


def test_search_returning(index, pseudo_ls8_type, pseudo_ls8_dataset, indexed_ls5_scene_dataset_types):
    """
    :type index: datacube.index._api.Index
    """

    # Expect one product with our one dataset.
    results = list(index.datasets.search_returning(
        ('id', 'sat_path', 'sat_row'),
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert len(results) == 1
    id, path_range, sat_range = results[0]
    assert id == pseudo_ls8_dataset.id
    # TODO: output nicer types?
    assert path_range == NumericRange(Decimal('116'), Decimal('116'), '[]')
    assert sat_range == NumericRange(Decimal('74'), Decimal('84'), '[]')


def test_search_returning_rows(index, pseudo_ls8_type,
                               pseudo_ls8_dataset, pseudo_ls8_dataset2,
                               indexed_ls5_scene_dataset_types):
    dataset = pseudo_ls8_dataset

    # If returning a field like uri, there will be one result per location.

    # No locations
    results = list(index.datasets.search_returning(
        ('id', 'uri'),
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert len(results) == 0

    # Add a location to the dataset and we should get one result
    test_uri = 'file:///tmp/test1'
    index.datasets.add_location(dataset, test_uri)
    results = list(index.datasets.search_returning(
        ('id', 'uri'),
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert len(results) == 1
    assert results == [(dataset.id, test_uri)]

    # Add a second location and we should get two results
    test_uri2 = 'file:///tmp/test2'
    index.datasets.add_location(dataset, test_uri2)
    results = set(index.datasets.search_returning(
        ('id', 'uri'),
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert len(results) == 2
    assert results == {
        (dataset.id, test_uri),
        (dataset.id, test_uri2)
    }

    # A second dataset now has a location too:
    test_uri3 = 'mdss://c10/tmp/something'
    index.datasets.add_location(pseudo_ls8_dataset2, test_uri3)
    # Datasets and locations should still correctly match up...
    results = set(index.datasets.search_returning(
        ('id', 'uri'),
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert len(results) == 3
    assert results == {
        (dataset.id, test_uri),
        (dataset.id, test_uri2),
        (pseudo_ls8_dataset2.id, test_uri3),
    }


def test_searches_only_type(index, pseudo_ls8_type, pseudo_ls8_dataset, ls5_nbar_gtiff_type):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_type: datacube.model.DatasetType
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    # The dataset should have been matched to the telemetry type.
    assert pseudo_ls8_dataset.type.id == pseudo_ls8_type.id
    assert index.datasets.search_eager()

    # One result in the telemetry type
    datasets = index.datasets.search_eager(
        product=pseudo_ls8_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # One result in the metadata type
    datasets = index.datasets.search_eager(
        metadata_type=pseudo_ls8_type.metadata_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # No results when searching for a different dataset type.
    datasets = index.datasets.search_eager(
        product=ls5_nbar_gtiff_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS'
    )
    assert len(datasets) == 0

    # One result when no types specified.
    datasets = index.datasets.search_eager(
        platform='LANDSAT_8',
        instrument='OLI_TIRS'
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # No results for different metadata type.
    datasets = index.datasets.search_eager(
        metadata_type='telemetry',
        platform='LANDSAT_8',
        instrument='OLI_TIRS'
    )
    assert len(datasets) == 0


def test_search_special_fields(index, pseudo_ls8_type, pseudo_ls8_dataset,
                               ls5_dataset_w_children):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_type: datacube.model.DatasetType
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """

    # 'product' is a special case
    datasets = index.datasets.search_eager(
        product=pseudo_ls8_type.name
    )
    assert len(datasets) == 1
    assert datasets[0].id == pseudo_ls8_dataset.id

    # Unknown field: no results
    datasets = index.datasets.search_eager(
        platform='LANDSAT_8',
        flavour='chocolate',
    )
    assert len(datasets) == 0


def test_search_conflicting_types(index, pseudo_ls8_dataset, pseudo_ls8_type):
    # Should return no results.
    datasets = index.datasets.search_eager(
        product=pseudo_ls8_type.name,
        # The telemetry type is not of type storage_unit.
        metadata_type='storage_unit'
    )
    assert len(datasets) == 0


def test_fetch_all_of_md_type(index, pseudo_ls8_dataset):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    # Get every dataset of the md type.
    results = index.datasets.search_eager(
        metadata_type='eo'
    )
    assert len(results) == 1
    assert results[0].id == pseudo_ls8_dataset.id
    # Get every dataset of the type.
    results = index.datasets.search_eager(
        product=pseudo_ls8_dataset.type.name
    )
    assert len(results) == 1
    assert results[0].id == pseudo_ls8_dataset.id

    # No results for another.
    results = index.datasets.search_eager(
        metadata_type='telemetry'
    )
    assert len(results) == 0


def test_count_searches(index, pseudo_ls8_type, pseudo_ls8_dataset, ls5_nbar_gtiff_type):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_type: datacube.model.DatasetType
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    # The dataset should have been matched to the telemetry type.
    assert pseudo_ls8_dataset.type.id == pseudo_ls8_type.id
    assert index.datasets.search_eager()

    # One result in the telemetry type
    datasets = index.datasets.count(
        product=pseudo_ls8_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    )
    assert datasets == 1

    # One result in the metadata type
    datasets = index.datasets.count(
        metadata_type=pseudo_ls8_type.metadata_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    )
    assert datasets == 1

    # No results when searching for a different dataset type.
    datasets = index.datasets.count(
        product=ls5_nbar_gtiff_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS'
    )
    assert datasets == 0

    # One result when no types specified.
    datasets = index.datasets.count(
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    )
    assert datasets == 1

    # No results for different metadata type.
    datasets = index.datasets.count(
        metadata_type='telemetry',
        platform='LANDSAT_8',
        instrument='OLI_TIRS'
    )
    assert datasets == 0


def test_get_dataset_with_children(index, ls5_dataset_w_children):
    # type: (Index, Dataset) -> None

    id_ = ls5_dataset_w_children.id
    assert isinstance(id_, UUID)

    # Sources not loaded by default
    d = index.datasets.get(id_)
    assert d.sources is None

    # Ask for all sources
    d = index.datasets.get(id_, include_sources=True)
    assert list(d.sources.keys()) == ['level1']
    level1 = d.sources['level1']
    assert list(level1.sources.keys()) == ['satellite_telemetry_data']
    assert list(level1.sources['satellite_telemetry_data'].sources) == []

    # It should also work with a string id
    d = index.datasets.get(str(id_), include_sources=True)
    assert list(d.sources.keys()) == ['level1']
    level1 = d.sources['level1']
    assert list(level1.sources.keys()) == ['satellite_telemetry_data']
    assert list(level1.sources['satellite_telemetry_data'].sources) == []


def test_count_by_product_searches(index, pseudo_ls8_type, pseudo_ls8_dataset, ls5_nbar_gtiff_type):
    """
    :type index: datacube.index._api.Index
    :type pseudo_ls8_type: datacube.model.DatasetType
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    # The dataset should have been matched to the telemetry type.
    assert pseudo_ls8_dataset.type.id == pseudo_ls8_type.id
    assert index.datasets.search_eager()

    # One result in the telemetry type
    products = tuple(index.datasets.count_by_product(
        product=pseudo_ls8_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert products == ((pseudo_ls8_type, 1),)

    # One result in the metadata type
    products = tuple(index.datasets.count_by_product(
        metadata_type=pseudo_ls8_type.metadata_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert products == ((pseudo_ls8_type, 1),)

    # No results when searching for a different dataset type.
    products = tuple(index.datasets.count_by_product(
        product=ls5_nbar_gtiff_type.name,
        platform='LANDSAT_8',
        instrument='OLI_TIRS'
    ))
    assert products == ()

    # One result when no types specified.
    products = tuple(index.datasets.count_by_product(
        platform='LANDSAT_8',
        instrument='OLI_TIRS',
    ))
    assert products == ((pseudo_ls8_type, 1),)

    # Only types with datasets should be returned (these params match ls5_gtiff too)
    products = tuple(index.datasets.count_by_product())
    assert products == ((pseudo_ls8_type, 1),)

    # No results for different metadata type.
    products = tuple(index.datasets.count_by_product(
        metadata_type='telemetry',
    ))
    assert products == ()


def test_count_time_groups(index, pseudo_ls8_type, pseudo_ls8_dataset):
    """
    :type index: datacube.index._api.Index
    """

    # 'from_dt': datetime.datetime(2014, 7, 26, 23, 48, 0, 343853),
    # 'to_dt': datetime.datetime(2014, 7, 26, 23, 52, 0, 343853),
    timeline = list(index.datasets.count_product_through_time(
        '1 day',
        product=pseudo_ls8_type.name,
        time=Range(
            datetime.datetime(2014, 7, 25, tzinfo=tz.tzutc()),
            datetime.datetime(2014, 7, 27, tzinfo=tz.tzutc())
        )
    ))

    assert len(timeline) == 2
    assert timeline == [
        (
            Range(datetime.datetime(2014, 7, 25, tzinfo=tz.tzutc()),
                  datetime.datetime(2014, 7, 26, tzinfo=tz.tzutc())),
            0
        ),
        (
            Range(datetime.datetime(2014, 7, 26, tzinfo=tz.tzutc()),
                  datetime.datetime(2014, 7, 27, tzinfo=tz.tzutc())),
            1
        )
    ]


@pytest.mark.usefixtures('default_metadata_type',
                         'indexed_ls5_scene_dataset_types')
def test_source_filter(global_integration_cli_args, index, example_ls5_dataset_path, ls5_nbar_ingest_config):
    opts = list(global_integration_cli_args)
    opts.extend(
        [
            '-v',
            'dataset',
            'add',
            '--auto-match',
            str(example_ls5_dataset_path)
        ]
    )
    result = CliRunner().invoke(
        datacube.scripts.cli_app.cli,
        opts,
        catch_exceptions=False
    )

    all_nbar = index.datasets.search_eager(product='ls5_nbar_scene')
    assert len(all_nbar) == 1

    dss = index.datasets.search_eager(
        product='ls5_nbar_scene',
        source_filter={'product': 'ls5_level1_scene', 'gsi': 'ASA'}
    )
    assert dss == all_nbar
    dss = index.datasets.search_eager(
        product='ls5_nbar_scene',
        source_filter={'product': 'ls5_level1_scene', 'gsi': 'GREG'}
    )
    assert dss == []

    with pytest.raises(RuntimeError):
        dss = index.datasets.search_eager(
            product='ls5_nbar_scene',
            source_filter={'gsi': 'ASA'}
        )


def test_count_time_groups_cli(global_integration_cli_args, pseudo_ls8_type, pseudo_ls8_dataset):
    # type: (list, DatasetType, Dataset) -> None

    opts = list(global_integration_cli_args)
    opts.extend(
        [
            'product-counts',
            '1 day',
            '2014-07-25 < time < 2014-07-27'
        ]
    )

    runner = CliRunner()
    result = runner.invoke(
        datacube.scripts.search_tool.cli,
        opts,
        catch_exceptions=False
    )
    assert result.exit_code == 0

    expected_out = (
        '{}\n'
        '    2014-07-25: 0\n'
        '    2014-07-26: 1\n'
    ).format(pseudo_ls8_type.name)

    assert result.output == expected_out


def test_search_cli_basic(global_integration_cli_args, telemetry_metadata_type, pseudo_ls8_dataset):
    """
    Search datasets using the cli.
    :type global_integration_cli_args: tuple[str]
    :type telemetry_metadata_type: datacube.model.MetadataType
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    opts = list(global_integration_cli_args)
    opts.extend(
        [
            # No search arguments: return all datasets.
            'datasets'
        ]
    )

    runner = CliRunner()
    result = runner.invoke(
        datacube.scripts.search_tool.cli,
        opts
    )
    assert str(pseudo_ls8_dataset.id) in result.output
    assert str(telemetry_metadata_type.name) in result.output

    assert result.exit_code == 0


def test_cli_info(index, global_integration_cli_args, pseudo_ls8_dataset, pseudo_ls8_dataset2):
    # type: (Index, tuple, Dataset, Dataset) -> None
    """
    Search datasets using the cli.
    :type index: datacube.index._api.Index
    :type global_integration_cli_args: tuple[str]
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    index.datasets.add_location(pseudo_ls8_dataset, 'file:///tmp/location1')
    index.datasets.add_location(pseudo_ls8_dataset, 'file:///tmp/location2')

    opts = list(global_integration_cli_args)
    opts.extend(
        [
            'dataset', 'info', str(pseudo_ls8_dataset.id)
        ]
    )

    runner = CliRunner()
    result = runner.invoke(
        datacube.scripts.cli_app.cli,
        opts,
        catch_exceptions=False
    )

    assert result.exit_code == 0
    output = result.output

    # Should be a valid yaml
    yaml_docs = list(yaml.safe_load_all(output))
    assert len(yaml_docs) == 1

    # We output properties in order for readability:
    output_lines = [l for l in output.splitlines() if not l.startswith('indexed:')]
    assert output_lines == [
        "id: " + str(pseudo_ls8_dataset.id),
        'product: ls8_telemetry',
        'status: active',
        # Newest location first
        'locations:',
        '- file:///tmp/location2',
        '- file:///tmp/location1',
        'fields:',
        '    gsi: null',
        '    instrument: OLI_TIRS',
        '    lat: {begin: -31.37116, end: -29.23394}',
        '    lon: {begin: 149.78434, end: 152.21782}',
        '    orbit: null',
        '    platform: LANDSAT_8',
        '    product_type: pseudo_ls8_data',
        '    sat_path: {begin: 116, end: 116}',
        '    sat_row: {begin: 74, end: 84}',
        "    time: {begin: '2014-07-26T23:48:00.343853', end: '2014-07-26T23:52:00.343853'}",
    ]

    # Check indexed time separately, as we don't care what timezone it's displayed in.
    indexed_time = yaml_docs[0]['indexed']
    assert isinstance(indexed_time, datetime.datetime)
    assert assume_utc(indexed_time) == assume_utc(pseudo_ls8_dataset.indexed_time)

    # Request two, they should have separate yaml documents
    opts.append(str(pseudo_ls8_dataset2.id))

    runner = CliRunner()
    result = runner.invoke(
        datacube.scripts.cli_app.cli,
        opts,
        catch_exceptions=False
    )
    yaml_docs = list(yaml.safe_load_all(result.output))
    assert len(yaml_docs) == 2, "Two datasets should produce two sets of info"
    assert yaml_docs[0]['id'] == str(pseudo_ls8_dataset.id)
    assert yaml_docs[1]['id'] == str(pseudo_ls8_dataset2.id)


def assume_utc(d):
    if d.tzinfo is None:
        return d.replace(tzinfo=tz.tzutc())
    else:
        return d.astimezone(tz.tzutc())


def test_cli_missing_info(global_integration_cli_args):
    opts = list(global_integration_cli_args)
    id_ = str(uuid.uuid4())
    opts.extend(
        [
            'dataset', 'info', id_
        ]
    )

    runner = CliRunner()
    result = runner.invoke(
        datacube.scripts.cli_app.cli,
        opts,
        catch_exceptions=False
    )

    assert result.exit_code == 1, "Should return exit status when dataset is missing"
    # This should have been output to stderr, but the CliRunner doesnit distinguish
    assert result.output == "{id} missing\n".format(id=id_)


def test_find_duplicates(index, pseudo_ls8_type,
                         pseudo_ls8_dataset, pseudo_ls8_dataset2, pseudo_ls8_dataset3, pseudo_ls8_dataset4,
                         ls5_dataset_w_children):
    # type: (Index, DatasetType, Dataset, Dataset, Dataset, Dataset, Dataset) -> None

    # Our four ls8 datasets and three ls5.
    all_datasets = index.datasets.search_eager()
    assert len(all_datasets) == 7

    # First two ls8 datasets have the same path/row, last two have a different row.
    expected_ls8_path_row_duplicates = [
        (
            (
                NumericRange(Decimal('116'), Decimal('116'), '[]'),
                NumericRange(Decimal('74'), Decimal('84'), '[]')
            ),
            {pseudo_ls8_dataset.id, pseudo_ls8_dataset2.id}
        ),
        (
            (
                NumericRange(Decimal('116'), Decimal('116'), '[]'),
                NumericRange(Decimal('85'), Decimal('87'), '[]')
            ),
            {pseudo_ls8_dataset3.id, pseudo_ls8_dataset4.id}
        ),

    ]

    # Specifying groups as fields:
    f = pseudo_ls8_type.metadata_type.dataset_fields.get
    field_res = sorted(index.datasets.search_product_duplicates(
        pseudo_ls8_type,
        f('sat_path'), f('sat_row')
    ))
    assert field_res == expected_ls8_path_row_duplicates
    # Field names as strings
    product_res = sorted(index.datasets.search_product_duplicates(
        pseudo_ls8_type,
        'sat_path', 'sat_row'
    ))
    assert product_res == expected_ls8_path_row_duplicates

    # Get duplicates that start on the same day
    f = pseudo_ls8_type.metadata_type.dataset_fields.get
    field_res = sorted(index.datasets.search_product_duplicates(
        pseudo_ls8_type,
        f('time').lower.day
    ))

    # Datasets 1 & 3 are on the 26th.
    # Datasets 2 & 4 are on the 27th.
    assert field_res == [
        (
            (
                datetime.datetime(2014, 7, 26, 0, 0),
            ),
            {pseudo_ls8_dataset.id, pseudo_ls8_dataset3.id}
        ),
        (
            (
                datetime.datetime(2014, 7, 27, 0, 0),
            ),
            {pseudo_ls8_dataset2.id, pseudo_ls8_dataset4.id}
        ),

    ]

    # No LS5 duplicates: there's only one of each
    sat_res = sorted(index.datasets.search_product_duplicates(
        ls5_dataset_w_children.type,
        'sat_path', 'sat_row'
    ))
    assert sat_res == []


def test_csv_search_via_cli(global_integration_cli_args, pseudo_ls8_type, pseudo_ls8_dataset, pseudo_ls8_dataset2):
    """
    Search datasets via the cli with csv output
    :type global_integration_cli_args: tuple[str]
    :type pseudo_ls8_dataset: datacube.model.Dataset
    """
    # Test dataset is:
    # platform: LANDSAT_8
    # from: 2014-7-26  23:48:00
    # to:   2014-7-26  23:52:00
    # coords:
    #     ll: (-31.33333, 149.78434)
    #     lr: (-31.37116, 152.20094)
    #     ul: (-29.23394, 149.85216)
    #     ur: (-29.26873, 152.21782)

    # Dataset 2 is the same but on day 2014-7-27

    rows = _cli_csv_search(['datasets', ' -40 < lat < -10'], global_integration_cli_args)
    assert len(rows) == 2
    assert {rows[0]['id'], rows[1]['id']} == {str(pseudo_ls8_dataset.id), str(pseudo_ls8_dataset2.id)}

    rows = _cli_csv_search(['datasets', 'product=' + pseudo_ls8_type.name], global_integration_cli_args)
    assert len(rows) == 2
    assert {rows[0]['id'], rows[1]['id']} == {str(pseudo_ls8_dataset.id), str(pseudo_ls8_dataset2.id)}

    # Don't return on a mismatch
    rows = _cli_csv_search(['datasets', '150<lat<160'], global_integration_cli_args)
    assert len(rows) == 0

    # Match only a single dataset using multiple fields
    rows = _cli_csv_search(['datasets', 'platform=LANDSAT_8', '2014-07-24<time<2014-07-27'],
                           global_integration_cli_args)
    assert len(rows) == 1
    assert rows[0]['id'] == str(pseudo_ls8_dataset.id)

    # One matching field, one non-matching
    rows = _cli_csv_search(['datasets', '2014-07-24<time<2014-07-27', 'platform=LANDSAT_5'],
                           global_integration_cli_args)
    assert len(rows) == 0


# Headers are currently in alphabetical order.
_EXPECTED_OUTPUT_HEADER = 'dataset_type_id,gsi,id,instrument,lat,lon,metadata_type,metadata_type_id,orbit,' \
                          'platform,product,product_type,sat_path,sat_row,time,uri'


def test_csv_structure(global_integration_cli_args, pseudo_ls8_type, ls5_nbar_gtiff_type,
                       pseudo_ls8_dataset, pseudo_ls8_dataset2):
    output = _csv_search_raw(['datasets', ' -40 < lat < -10'], global_integration_cli_args)
    lines = [line.strip() for line in output.split('\n') if line]
    # A header and two dataset rows
    assert len(lines) == 3

    assert lines[0] == _EXPECTED_OUTPUT_HEADER


def _cli_csv_search(args, global_integration_cli_args):
    # Do a CSV search from the cli, returning results as a list of dictionaries
    output = _csv_search_raw(args, global_integration_cli_args)
    return list(csv.DictReader(io.StringIO(output)))


def _csv_search_raw(args, global_integration_cli_args):
    # Do a CSV search from the cli, returning output as a string
    global_opts = list(global_integration_cli_args)
    global_opts.extend(['-f', 'csv'])
    result = _cli_search(args, global_opts)
    assert result.exit_code == 0, result.output
    return result.output


def _cli_search(args, global_integration_cli_args):
    opts = list(global_integration_cli_args)
    opts.extend(args)
    runner = CliRunner()
    result = runner.invoke(
        datacube.scripts.search_tool.cli,
        opts,
        catch_exceptions=False
    )
    return result
