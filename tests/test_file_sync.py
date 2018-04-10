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

"""Test suite for `cntosync.file_sync`."""

import os
from unittest.mock import call

import cntosync.configuration as config
import cntosync.file_sync as unit

import pytest


class CommonMock(object):
    """Mock functions common to `unit.Repository.initialize`."""

    def __init__(self, mocker):  # noqa: D401
        """Setup mocks."""
        self.mock_path_isdir = mocker.patch('os.path.isdir')
        self.mock_makedirs = mocker.patch('os.makedirs')
        self.mock_open = mocker.patch('builtins.open')
        self.mock_check_presence = mocker.patch('cntosync.file_sync.Repository.check_presence')
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
    uri = ''

    common_mock.mock_path_isdir.return_value = True
    common_mock.mock_check_presence.return_value = False

    unit.Repository.initialize(directory, name, uri)

    common_mock.mock_makedirs.assert_called_with(os.path.join(directory, config.index_directory),
                                                 exist_ok=True)
    common_mock.mock_open.assert_called_with(os.path.join(directory, config.index_directory,
                                                          config.index_file), mode='wb')


def test_init_repo_index_ok(common_mock):
    """Assert index file contains the needed data."""
    directory = '/test'
    name = 'repositorytestname'
    uri = 'some:/uri/to/repo'
    index_data = {'display_name': name, 'uri': uri, 'configuration_version': config.version,
                  'index_file_name': config.index_file, 'sync_file_extension': config.extension}

    common_mock.mock_path_isdir.return_value = True
    common_mock.mock_check_presence.return_value = False

    unit.Repository.initialize(directory, name, uri)

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
    uri = ''

    common_mock.mock_path_isdir.return_value = True
    common_mock.mock_check_presence.return_value = True

    unit.Repository.initialize(directory, name, uri, overwrite)

    if not overwrite:
        common_mock.mock_makedirs.assert_not_called()
    else:
        common_mock.mock_makedirs.assert_called()


def test_init_repo_not_dir(common_mock):
    """Assert directory is created if not existing."""
    directory = '/test'
    name = ''
    uri = ''

    common_mock.mock_path_isdir.return_value = False
    common_mock.mock_check_presence.return_value = False

    unit.Repository.initialize(directory, name, uri)

    common_mock.mock_makedirs.assert_any_call(directory, exist_ok=True)


def test_init_repo_permission_denied(common_mock):
    """Assert error is raised if invalid permissions to create a directory."""
    directory = '/test'
    name = ''
    uri = ''

    common_mock.mock_path_isdir.return_value = False
    common_mock.mock_check_presence.return_value = False
    common_mock.mock_makedirs.side_effect = PermissionError

    with pytest.raises(PermissionError):
        unit.Repository.initialize(directory, name, uri)
