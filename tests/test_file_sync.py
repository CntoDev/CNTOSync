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

import cntosync.file_sync as unit

import pytest


@pytest.fixture()
def config(mocker):
    """Fixture for object of type `configuration.Configuration`."""
    config = mocker.Mock()
    config.index_directory = 'bbbbbbb'
    config.index_file = 'aaaaa'
    config.version = 'ccc'
    config.extension = 'dd'

    return config


@pytest.mark.parametrize('os_return_values,unit_return_value', [
    (((True, True), True), True),
    (((False, True), True), False),
])
def test_is_repository(os_return_values, unit_return_value, config, mocker):
    """Assert function returns True if directory is repository, False otherwise."""
    mocker.patch('os.path.isdir', side_effect=os_return_values[0])
    mocker.patch('os.path.isfile', return_value=os_return_values[1])

    assert unit.is_repository('/test', config) == unit_return_value


def test_init_repo_creation_ok(config, mocker):
    """Assert directories and files are created."""
    dir = '/test'  # noqa: A001
    name = ''
    uri = ''

    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('cntosync.file_sync.is_repository', return_value=False)
    mocker.patch('msgpack.packb')
    mock_os_makedirs = mocker.patch('os.makedirs')
    mock_open = mocker.patch('builtins.open')

    unit.initialize_repository(dir, config, name, uri)

    mock_os_makedirs.assert_called_with(os.path.join(dir, config.index_directory), exist_ok=True)
    mock_open.assert_called_with(os.path.join(dir, config.index_directory, config.index_file),
                                 mode='wb')


def test_init_repo_index_ok(config, mocker):
    """Assert index file contains the needed data."""
    dir = '/test'  # noqa: A001
    name = 'repositorytestname'
    uri = 'some:/uri/to/repo'
    index_data = {'display_name': name, 'uri': uri, 'configuration_version': config.version,
                  'index_file_name': config.index_file, 'sync_file_extension': config.extension}

    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('cntosync.file_sync.is_repository', return_value=False)
    mocker.patch('os.makedirs')
    mock_packb = mocker.patch('msgpack.packb')
    mock_open = mocker.patch('builtins.open')

    unit.initialize_repository(dir, config, name, uri)

    mock_open.return_value.__enter__.return_value.write.assert_called()
    mock_packb.assert_called_once()
    assert mock_packb.call_args == call(index_data)


@pytest.mark.parametrize('overwrite', [
    True,
    False,
])
def test_init_repo_overwrite(overwrite, config, mocker):
    """Assert repository is re-initialized if overwrite enabled, assert not changed otherwise."""
    dir = '/test'  # noqa: A001
    name = ''
    uri = ''

    mocker.patch('cntosync.file_sync.is_repository', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('builtins.open')
    mock_makedirs = mocker.patch('os.makedirs')

    unit.initialize_repository(dir, config, name, uri, overwrite)

    if not overwrite:
        mock_makedirs.assert_not_called()
    else:
        mock_makedirs.assert_called()


def test_init_repo_not_dir(config, mocker):
    """Assert directory is created if not existing."""
    dir = '/test'  # noqa: A001
    name = ''
    uri = ''

    mocker.patch('os.path.isdir', return_value=False)
    mock_makedirs = mocker.patch('os.makedirs')
    mocker.patch('cntosync.file_sync.is_repository', return_value=False)
    mocker.patch('builtins.open')

    unit.initialize_repository(dir, config, name, uri)

    mock_makedirs.assert_any_call(dir, exist_ok=True)


def test_init_repo_permission_denied(config, mocker):
    """Assert error is raised if invalid permissions to create a directory."""
    dir = '/test'  # noqa: A001
    name = ''
    uri = ''

    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('os.makedirs', side_effect=PermissionError)
    mocker.patch('cntosync.file_sync.is_repository', return_value=False)
    mocker.patch('builtins.open')

    with pytest.raises(PermissionError):
        unit.initialize_repository(dir, config, name, uri)
