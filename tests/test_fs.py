import pytest
import asyncio

from esgpull.types import File
from esgpull.fs import Filesystem


@pytest.fixture
def fs(tmp_path):
    return Filesystem(tmp_path)


@pytest.fixture
def file(fs):
    f = File(
        file_id="file",
        dataset_id="dataset",
        master_id="master",
        url="file",
        version="v0",
        filename="file.nc",
        local_path=str(fs.data),
        data_node="data_node",
        checksum="0",
        checksum_type="0",
        size=0,
    )
    f.id = 1
    return f


@pytest.fixture
def writer(fs, file):
    return fs.make_writer(file)


def test_fs(tmp_path, fs):
    assert str(fs.data) == str(tmp_path / "data")
    assert str(fs.db) == str(tmp_path / "db")
    assert fs.data.is_dir()
    assert fs.data.is_dir()


def test_file_paths(fs, file):
    assert fs.path_of(file) == fs.data / "file.nc"
    assert fs.tmp_path_of(file) == fs.tmp / "1.file.nc"


async def writer_steps(writer):
    async with writer.open() as write:
        await write(b"")


def test_fs_writer(fs, file, writer):
    asyncio.run(writer_steps(writer))
    assert list(fs.glob_netcdf()) == [fs.path_of(file)]
