# --------------------------------License Notice----------------------------------
# CNTOSync - Carpe Noctem Tactical Operations ArmA3 mod synchronization tool
# Copyright (C) 2018 Carpe Noctem - Tactical Operations (aka. CNTO) (contact@carpenoctem.co)
#
# The authors of this software are listed in the AUTHORS file at the
# root of this software's source code tree.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# All rights reserved.
# --------------------------------License Notice----------------------------------

"""Test suite for `cntosync.filesync`."""

import os
import random
import zlib
from unittest.mock import call

import cntosync.configuration as config
import cntosync.filesync as unit
from cntosync import exceptions

import pytest


test_dir_structure = (
    ('/testdir', ('subdir_1', 'subdir_2'), ('root_file_1', 'root_file_2.txt')),
    ('/testdir/subdir_1', ('s_subdir_1'), ('subdir_1_file_1.txt', 'subdir_1_file_2')),
    ('/testdir/subdir_2', (), ('subdir_2_file_1.bb', 'subdir_2_file_2.aa')),
    ('/testdir/subdir_1/s_subdir_1', (), ('s_subdir_1_file_1',)),
)

test_file_contents = {
    'root_file_1': 'aaaa',
    'root_file_2.txt': 'bbbb',
    'subdir_1_file_1.txt': 'cccc',
    'subdir_1_file_2': 'ddddd',
    'subdir_2_file_1.bb': 'eeeee',
    'subdir_2_file_2.aa': 'fffff',
    's_subdir_1_file_1': 'gggggggggg',
}

test_file_paths = (
    '/testdir/root_file_1',
    '/testdir/root_file_2.txt',
    '/testdir/subdir_1/subdir_1_file_1.txt',
    '/testdir/subdir_1/subdir_1_file_2',
    '/testdir/subdir_2/subdir_2_file_1.bb',
    '/testdir/subdir_2/subdir_2_file_2.aa',
    '/testdir/subdir_1/s_subdir_1/s_subdir_1_file_1',
)


class CommonMock(object):
    """Mock functions common to `unit.Repository.initialize`."""

    def __init__(self, mocker):  # noqa: D401
        """Setup mocks."""
        self.mock_path_isdir = mocker.patch('os.path.isdir')
        self.mock_makedirs = mocker.patch('os.makedirs')
        self.mock_open = mocker.patch('builtins.open')
        self.mock_valid_url = mocker.patch('cntosync.filesync.valid_url', return_value=True)
        self.mock_check_presence = mocker.patch('cntosync.filesync.Repository.check_presence')
        self.mock_packb = mocker.patch('msgpack.packb')


@pytest.fixture()
def common_mock(mocker) -> CommonMock:
    """Offer `InitRepoMock` as pytest fixture."""
    return CommonMock(mocker)


@pytest.mark.parametrize('os_return_values,unit_return_value', [
    (((True, True), True), True),
    (((False, True), True), False),
])
def test_check_presence(os_return_values, unit_return_value, mocker):
    """Assert function returns True if directory is repository, False otherwise."""
    mocker.patch('os.path.isdir', side_effect=os_return_values[0])
    mocker.patch('os.path.isfile', return_value=os_return_values[1])

    assert unit.Repository.check_presence('/test') == unit_return_value


def test_init_repo_creation_ok(common_mock):
    """Assert directories and files are created."""
    directory = '/test'
    name = ''
    url = 'file://something'

    common_mock.mock_path_isdir.return_value = True
    common_mock.mock_check_presence.return_value = False

    unit.Repository.initialize(directory, name, url)

    common_mock.mock_makedirs.assert_called_with(os.path.join(directory, config.index_directory),
                                                 exist_ok=True)
    common_mock.mock_open.assert_called_with(os.path.join(directory, config.index_directory,
                                                          config.index_file), mode='wb')


def test_init_repo_index_ok(common_mock):
    """Assert index file contains the needed data."""
    directory = '/test'
    name = 'repositorytestname'
    url = 'file://something'
    index_data = {'display_name': name, 'url': url, 'configuration_version': config.version,
                  'index_file_name': config.index_file, 'sync_file_extension': config.extension}

    common_mock.mock_path_isdir.return_value = True
    common_mock.mock_check_presence.return_value = False

    unit.Repository.initialize(directory, name, url)

    common_mock.mock_open.return_value.__enter__.return_value.write.assert_called()
    common_mock.mock_packb.assert_called_once()
    assert common_mock.mock_packb.call_args == call(index_data)


@pytest.mark.parametrize('overwrite', [
    True,
    False,
])
def test_init_repo_overwrite(overwrite, common_mock):
    """Assert repository is re-initialized if overwrite enabled, assert not changed otherwise."""
    directory = '/test'
    name = ''
    url = 'file://something'

    common_mock.mock_path_isdir.return_value = True
    common_mock.mock_check_presence.return_value = True

    unit.Repository.initialize(directory, name, url, overwrite)

    if not overwrite:
        common_mock.mock_makedirs.assert_not_called()
    else:
        common_mock.mock_makedirs.assert_called()


def test_init_repo_not_dir(common_mock):
    """Assert directory is created if not existing."""
    directory = '/test'
    name = ''
    url = 'file://something'

    common_mock.mock_path_isdir.return_value = False
    common_mock.mock_check_presence.return_value = False

    unit.Repository.initialize(directory, name, url)

    common_mock.mock_makedirs.assert_any_call(directory, exist_ok=True)


def test_init_repo_permission_denied(common_mock):
    """Assert error is raised if invalid permissions to create a directory."""
    directory = '/test'
    name = ''
    url = 'file://something'

    common_mock.mock_path_isdir.return_value = False
    common_mock.mock_check_presence.return_value = False
    common_mock.mock_makedirs.side_effect = PermissionError

    with pytest.raises(PermissionError):
        unit.Repository.initialize(directory, name, url)


def test_init_repo_unsupported_schema():
    """Assert exception is raised if unsupported url schema is passed."""
    directory = '/test'
    name = ''
    url = 'sftp://something'

    with pytest.raises(exceptions.UnsupportedURLSchema):
        unit.Repository.initialize(directory, name, url)


@pytest.mark.parametrize('url', [
    'http://',
    'ftp:/malformed',
    '://onlyhost',
])
def test_init_repo_invalid_url(url):
    """Assert exception is raised if invalid url is passed."""
    directory = '/test'
    name = ''

    with pytest.raises(exceptions.InvalidURL):
        unit.Repository.initialize(directory, name, url)


def test_list_files_nominal(mocker):
    """Assert function returns correct list of files."""
    mocker.patch('os.walk', return_value=test_dir_structure)

    files = unit.list_files(test_dir_structure[0][0])

    assert len(files) == len(test_file_contents)
    for path in test_file_paths:
        assert path in files


def test_list_files_bl_subdirs(mocker):
    """Assert files in blacklisted directories are not listed."""
    mocker.patch('os.walk', return_value=test_dir_structure)

    files = unit.list_files(test_dir_structure[0][0], bl_subdirs=('subdir_1',))

    assert len(files) == (len(test_file_paths) - 3)
    for file in files:
        assert 'subdir_1' not in file


def test_list_files_bl_extensions(mocker):
    """Assert files with blacklisted extension are not listed."""
    mocker.patch('os.walk', return_value=test_dir_structure)

    files = unit.list_files(test_dir_structure[0][0], bl_extensions=('.txt',))

    assert len(files) == (len(test_file_paths) - 2)
    for file in files:
        assert '.txt' not in file


@pytest.mark.parametrize('content_size', [
    0,
    4096,
    102400,
])
def test_file_checksum(tmpdir, content_size):
    """Assert checksums calculated over the content of a file are correct."""
    random.seed(a=42)

    file_content = bytearray(random.getrandbits(8) for _ in range(content_size))
    file_path = tmpdir.join('file_checksum_test')

    file_path.write_binary(file_content)

    assert unit.file_checksum(file_path) == zlib.adler32(file_content)


def test_repository_init(mocker):
    """Assert configuration is properly loaded when instancing the class."""
    repo = unit.Repository('/repository',
                           index_directory='indexhere',
                           index_filename='repoindex',
                           metafile_extension='filext')

    assert repo.repo_path == '/repository'
    assert repo.index_directory == 'indexhere'
    assert repo._index_path == '/repository/indexhere'
    assert repo._index_file_path == 'repoindex'
    assert repo._sync_file_extension == 'filext'
    assert repo.settings == {}
    assert repo.file_checksums == {}
