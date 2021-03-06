
from __future__ import absolute_import

try:
    import cPickle as pickle
except ImportError:
    import pickle

from datacube.utils import geometry


def test_pickleable():
    poly = geometry.polygon([(10, 20), (20, 20), (20, 10), (10, 20)], crs=geometry.CRS('EPSG:4326'))
    pickled = pickle.dumps(poly, pickle.HIGHEST_PROTOCOL)
    unpickled = pickle.loads(pickled)
    assert poly == unpickled


def test_props():
    box1 = geometry.box(10, 10, 30, 30, crs=geometry.CRS('EPSG:4326'))
    assert box1
    assert box1.is_valid
    assert not box1.is_empty
    assert box1.area == 400.0
    assert box1.boundary.length == 80.0
    assert box1.centroid == geometry.point(20, 20, geometry.CRS('EPSG:4326'))

    triangle = geometry.polygon([(10, 20), (20, 20), (20, 10), (10, 20)], crs=geometry.CRS('EPSG:4326'))
    assert triangle.envelope == geometry.BoundingBox(10, 10, 20, 20)

    outer = next(iter(box1))
    assert outer.length == 80.0

    box1copy = geometry.box(10, 10, 30, 30, crs=geometry.CRS('EPSG:4326'))
    assert box1 == box1copy
    assert box1.convex_hull == box1copy  # NOTE: this might fail because of point order

    box2 = geometry.box(20, 10, 40, 30, crs=geometry.CRS('EPSG:4326'))
    assert box1 != box2


def test_tests():
    box1 = geometry.box(10, 10, 30, 30, crs=geometry.CRS('EPSG:4326'))
    box2 = geometry.box(20, 10, 40, 30, crs=geometry.CRS('EPSG:4326'))
    box3 = geometry.box(30, 10, 50, 30, crs=geometry.CRS('EPSG:4326'))
    box4 = geometry.box(40, 10, 60, 30, crs=geometry.CRS('EPSG:4326'))
    minibox = geometry.box(15, 15, 25, 25, crs=geometry.CRS('EPSG:4326'))

    assert not box1.touches(box2)
    assert box1.touches(box3)
    assert not box1.touches(box4)

    assert box1.intersects(box2)
    assert box1.intersects(box3)
    assert not box1.intersects(box4)

    assert not box1.crosses(box2)
    assert not box1.crosses(box3)
    assert not box1.crosses(box4)

    assert not box1.disjoint(box2)
    assert not box1.disjoint(box3)
    assert box1.disjoint(box4)

    assert box1.contains(minibox)
    assert not box1.contains(box2)
    assert not box1.contains(box3)
    assert not box1.contains(box4)

    assert minibox.within(box1)
    assert not box1.within(box2)
    assert not box1.within(box3)
    assert not box1.within(box4)


def test_ops():
    box1 = geometry.box(10, 10, 30, 30, crs=geometry.CRS('EPSG:4326'))
    box2 = geometry.box(20, 10, 40, 30, crs=geometry.CRS('EPSG:4326'))
    box4 = geometry.box(40, 10, 60, 30, crs=geometry.CRS('EPSG:4326'))

    union1 = box1.union(box2)
    assert union1.area == 600.0

    inter1 = box1.intersection(box2)
    assert bool(inter1)
    assert inter1.area == 200.0

    inter2 = box1.intersection(box4)
    assert not bool(inter2)
    assert inter2.is_empty
    # assert not inter2.is_valid  TODO: what's going on here?

    diff1 = box1.difference(box2)
    assert diff1.area == 200.0

    symdiff1 = box1.symmetric_difference(box2)
    assert symdiff1.area == 400.0


def test_unary_union():
    box1 = geometry.box(10, 10, 30, 30, crs=geometry.CRS('EPSG:4326'))
    box2 = geometry.box(20, 10, 40, 30, crs=geometry.CRS('EPSG:4326'))
    box3 = geometry.box(30, 10, 50, 30, crs=geometry.CRS('EPSG:4326'))
    box4 = geometry.box(40, 10, 60, 30, crs=geometry.CRS('EPSG:4326'))

    union0 = geometry.unary_union([box1])
    assert union0 == box1

    union1 = geometry.unary_union([box1, box4])
    assert union1.type == 'MultiPolygon'
    assert union1.area == 2.0*box1.area

    union2 = geometry.unary_union([box1, box2])
    assert union2.type == 'Polygon'
    assert union2.area == 1.5*box1.area

    union3 = geometry.unary_union([box1, box2, box3, box4])
    assert union3.type == 'Polygon'
    assert union3.area == 2.5*box1.area

    union4 = geometry.unary_union([union1, box2, box3])
    assert union4.type == 'Polygon'
    assert union4.area == 2.5*box1.area


def test_unary_intersection():
    box1 = geometry.box(10, 10, 30, 30, crs=geometry.CRS('EPSG:4326'))
    box2 = geometry.box(15, 10, 35, 30, crs=geometry.CRS('EPSG:4326'))
    box3 = geometry.box(20, 10, 40, 30, crs=geometry.CRS('EPSG:4326'))
    box4 = geometry.box(25, 10, 45, 30, crs=geometry.CRS('EPSG:4326'))
    box5 = geometry.box(30, 10, 50, 30, crs=geometry.CRS('EPSG:4326'))
    box6 = geometry.box(35, 10, 55, 30, crs=geometry.CRS('EPSG:4326'))

    inter1 = geometry.unary_intersection([box1])
    assert bool(inter1)
    assert inter1 == box1

    inter2 = geometry.unary_intersection([box1, box2])
    assert bool(inter2)
    assert inter2.area == 300.0

    inter3 = geometry.unary_intersection([box1, box2, box3])
    assert bool(inter3)
    assert inter3.area == 200.0

    inter4 = geometry.unary_intersection([box1, box2, box3, box4])
    assert bool(inter4)
    assert inter4.area == 100.0

    inter5 = geometry.unary_intersection([box1, box2, box3, box4, box5])
    assert bool(inter5)
    assert inter5.type == 'LineString'
    assert inter5.length == 20.0

    inter6 = geometry.unary_intersection([box1, box2, box3, box4, box5, box6])
    assert not bool(inter6)
    assert inter6.is_empty


def test_crs_equality():
    a = geometry.CRS("""PROJCS["unnamed",GEOGCS["Unknown datum based upon the custom spheroid",
                       DATUM["Not specified (based on custom spheroid)",SPHEROID["Custom spheroid",6371007.181,0]],
                       PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Sinusoidal"],
                       PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],
                       PARAMETER["false_northing",0],UNIT["Meter",1]]""")
    b = geometry.CRS("""PROJCS["unnamed",GEOGCS["unnamed ellipse",DATUM["unknown",SPHEROID["unnamed",6371007.181,0]],
                       PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Sinusoidal"],
                       PARAMETER["longitude_of_center",0],PARAMETER["false_easting",0],
                       PARAMETER["false_northing",0],UNIT["Meter",1]]""")
    c = geometry.CRS('+a=6371007.181 +b=6371007.181 +units=m +y_0=0 +proj=sinu +lon_0=0 +no_defs +x_0=0')
    assert a == b
    assert a == c
    assert b == c

    assert a != geometry.CRS('EPSG:4326')

    a = geometry.CRS("""GEOGCS["GEOCENTRIC DATUM of AUSTRALIA",DATUM["GDA94",SPHEROID["GRS80",6378137,298.257222101]],
                        PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]""")
    b = geometry.CRS("""GEOGCS["GRS 1980(IUGG, 1980)",DATUM["unknown",SPHEROID["GRS80",6378137,298.257222101]],
                        PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]""")
    c = geometry.CRS('+proj=longlat +no_defs +ellps=GRS80')
    assert a == b
    assert a == c
    assert b == c


def test_geobox():
    points_list = [
        [(148.2697, -35.20111), (149.31254, -35.20111), (149.31254, -36.331431), (148.2697, -36.331431)],
        [(148.2697, 35.20111), (149.31254, 35.20111), (149.31254, 36.331431), (148.2697, 36.331431)],
        [(-148.2697, 35.20111), (-149.31254, 35.20111), (-149.31254, 36.331431), (-148.2697, 36.331431)],
        [(-148.2697, -35.20111), (-149.31254, -35.20111), (-149.31254, -36.331431), (-148.2697, -36.331431),
         (148.2697, -35.20111)],
        ]
    for points in points_list:
        polygon = geometry.polygon(points, crs=geometry.CRS('EPSG:3577'))
        resolution = (-25, 25)
        geobox = geometry.GeoBox.from_geopolygon(polygon, resolution)

        assert abs(resolution[0]) > abs(geobox.extent.boundingbox.left - polygon.boundingbox.left)
        assert abs(resolution[0]) > abs(geobox.extent.boundingbox.right - polygon.boundingbox.right)
        assert abs(resolution[1]) > abs(geobox.extent.boundingbox.top - polygon.boundingbox.top)
        assert abs(resolution[1]) > abs(geobox.extent.boundingbox.bottom - polygon.boundingbox.bottom)
