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
from unittest.mock import call

import cntosync.configuration as config
import cntosync.filesync as unit
from cntosync import exceptions

import pytest


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


testdir_contents = {'root_file_1': 'foo', 'root_file_2': 'bar', 'subdir_1_file_1': 'something',
                    'subdir_1_file_2': 'aaaaaa', 'subdir_2_file_1': 'somecontent',
                    'subdir_2_file_2': 'moreofit'}
testdir_paths = []


@pytest.fixture(scope='session')
def testdir(tmpdir_factory):
    """Return a temporary directory populated with test files and subdirectories."""
    root = tmpdir_factory.getbasetemp()
    subdir0 = tmpdir_factory.mktemp('subdir', numbered=True)
    subdir1 = tmpdir_factory.mktemp('subdir', numbered=True)
    root_file_1 = root.join('root_file_1')
    root_file_2 = root.join('root_file_2.txt')
    subdir_1_file_1 = subdir0.join('subdir_1_file_1.pdf')
    subdir_1_file_2 = subdir0.join('subdir_1_file_2.md')
    subdir_2_file_1 = subdir1.join('subdir_2_file_1')
    subdir_2_file_2 = subdir1.join('subdir_2_file_2.txt')

    root_file_1.write(testdir_contents['root_file_1'])
    root_file_2.write(testdir_contents['root_file_2'])
    subdir_1_file_1.write(testdir_contents['subdir_1_file_1'])
    subdir_1_file_2.write(testdir_contents['subdir_1_file_2'])
    subdir_2_file_1.write(testdir_contents['subdir_2_file_1'])
    subdir_2_file_2.write(testdir_contents['subdir_2_file_2'])

    testdir_paths.append(str(root_file_1))
    testdir_paths.append(str(root_file_2))
    testdir_paths.append(str(subdir_1_file_1))
    testdir_paths.append(str(subdir_1_file_2))
    testdir_paths.append(str(subdir_2_file_1))
    testdir_paths.append(str(subdir_2_file_2))

    return root


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


def test_list_files_nominal(testdir):
    """Assert function returns correct list of files."""
    files = unit.list_files(str(testdir))

    assert len(testdir_paths) == len(files)
    for file in files:
        assert file in testdir_paths


def test_list_files_bl_subdirs(testdir):
    """Assert files in blacklisted directories are not listed."""
    files = unit.list_files(str(testdir), bl_subdirs='subdir0')

    assert len(files) == (len(testdir_paths) - 2)
    for file in files:
        assert 'subdir0' not in file


def test_list_files_bl_extensions(testdir):
    """Assert files with blacklisted extension are not listed"""
    files = unit.list_files(str(testdir), bl_extensions='.txt')

    assert len(files) == (len(testdir_paths) - 2)
    for file in files:
        assert '.txt' not in file
