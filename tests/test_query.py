import pytest
import yaml

from esgpull.exceptions import FacetNameError
from esgpull.query import Query


@pytest.fixture
def q():
    return Query()


def test_configure():
    Query.configure(facets=["a", "b"], extra=[])
    q = Query()
    assert len(q._facets) == 2
    with pytest.raises(FacetNameError):
        q.mip_era
    Query.configure()  # reset to default facets
    q.mip_era  # no raise now


def test_empty_dump(q):
    assert q.dump() == {}


def test_setattr_setitem_iadd(q):
    q.project = "CMIP6"
    q["mip_era"] = "CMIP6"
    assert q.dump() == {"project": "CMIP6", "mip_era": "CMIP6"}


def test_iadd(q):
    q.variable = "one", "two"
    q.variable + ["two", "three"]
    assert len(q.variable.values) == 3


def test_unknown_facet_get_set(q):
    with pytest.raises(FacetNameError):
        q.not_a_facet
    with pytest.raises(FacetNameError):
        q.not_a_facet = "value"


def test_iter_len(q):
    q.project = "CMIP6"
    q.mip_era = "CMIP6"
    q.mip_era + "CMIP5"
    assert len(q) == 2
    names = sorted(facet.name for facet in q)
    assert names == ["mip_era", "project"]


def test_clone_is_deepcopy(q):
    q.project = "CMIP6"
    clone = q.clone()
    assert q.dump() == clone.dump()
    clone.project = "CMIP5"
    assert q.dump() != clone.dump()


def test_add(q):
    # various ways to create subqueries
    a = q.add()
    b = Query()
    c = q.clone()
    d = q.tosimple()
    q.project = "CMIP6"
    a.mip_era = "CMIP6"
    b.variable = "value1"
    c.project + "CMIP5"
    d.variable = "value2"
    q.add(b)
    q.add(c)
    q.add(d)
    assert q.dump() == {
        "project": "CMIP6",
        "requests": [
            {"mip_era": "CMIP6"},
            {"variable": "value1"},
            {"+project": "CMIP5"},
            {"variable": "value2"},
        ],
    }


def test_update():
    a = Query()
    b = Query()
    a.project = "CMIP6"
    b.mip_era = "CMIP6"
    b.project + "CMIP5"
    a.update(b)
    assert a.dump() == {"+project": ["CMIP5", "CMIP6"], "mip_era": "CMIP6"}
    c = Query()
    c.mip_era = "CORDEX"
    d = c.add()
    d.variable = "value"
    a.update(c)
    assert a.dump() == {
        "+project": ["CMIP5", "CMIP6"],
        "mip_era": "CORDEX",
        "requests": [{"variable": "value"}],
    }


def test_flatten(q):
    q.project = "CMIP6"
    q.variable = "value1"
    flat_dump = [flat.dump() for flat in q.flatten()]
    assert flat_dump == [q.dump()]
    a = q.add()
    b = q.add()
    a.project = "CMIP5"
    b.variable + "value2"
    flat_dump = [flat.dump() for flat in q.flatten()]
    assert flat_dump == [
        {"project": "CMIP5", "variable": "value1"},
        {"project": "CMIP6", "variable": ["value1", "value2"]},
    ]


def test_from_file(tmp_path):
    source = {
        "project": "CMIP6",
        "requests": [{"mip_era": "CMIP5"}, {"mip_era": "CMIP6"}],
    }
    source_file = tmp_path / "source.yaml"
    with open(source_file, "w") as f:
        f.write(yaml.dump(source))
    q = Query.from_file(source_file)
    assert q.dump() == source


def test_example(q):
    # Set facets using `=`
    q.project = "CMIP5"
    q.experiment = "historical"
    q.ensemble = "r1i1p1"
    q.realm = "atmos"
    q.time_frequency = "day"

    a = q.add()
    # Appending to previously set facet is done with `+`
    a.experiment + "rcp26"
    # Setting the facet with `=` replaces the previous value
    a.time_frequency = "mon"
    a.variable = "tasmin"

    b = q.add()
    b.experiment = "rcp85"
    b.variable = ["tas", "ua"]

    c = q.add()
    c.time_frequency + ["mon", "fx"]
    c.variable = "tasmax"

    assert q.dump() == {
        "ensemble": "r1i1p1",
        "experiment": "historical",
        "project": "CMIP5",
        "realm": "atmos",
        "requests": [
            {
                "+experiment": "rcp26",
                "time_frequency": "mon",
                "variable": "tasmin",
            },
            {"experiment": "rcp85", "variable": ["tas", "ua"]},
            {"+time_frequency": ["fx", "mon"], "variable": "tasmax"},
        ],
        "time_frequency": "day",
    }

    assert [flat.dump() for flat in q.flatten()] == [
        {
            "ensemble": "r1i1p1",
            "experiment": ["historical", "rcp26"],
            "project": "CMIP5",
            "realm": "atmos",
            "time_frequency": "mon",
            "variable": "tasmin",
        },
        {
            "ensemble": "r1i1p1",
            "experiment": "rcp85",
            "project": "CMIP5",
            "realm": "atmos",
            "time_frequency": "day",
            "variable": ["tas", "ua"],
        },
        {
            "ensemble": "r1i1p1",
            "experiment": "historical",
            "project": "CMIP5",
            "realm": "atmos",
            "time_frequency": ["day", "fx", "mon"],
            "variable": "tasmax",
        },
    ]
