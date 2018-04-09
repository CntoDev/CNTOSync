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


@pytest.mark.parametrize('os_return_values,unit_return_value', [
    (((True, True), True), True),
    (((False, True), True), False),
])
def test_check_presence(os_return_values, unit_return_value, mocker):
    """Assert function returns True if directory is repository, False otherwise."""
    mocker.patch('os.path.isdir', side_effect=os_return_values[0])
    mocker.patch('os.path.isfile', return_value=os_return_values[1])

    assert unit.Repository.check_presence('/test') == unit_return_value


def test_init_repo_creation_ok(mocker):
    """Assert directories and files are created."""
    directory = '/test'
    name = ''
    uri = ''

    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('cntosync.file_sync.Repository.check_presence', return_value=False)
    mocker.patch('msgpack.packb')
    mock_os_makedirs = mocker.patch('os.makedirs')
    mock_open = mocker.patch('builtins.open')

    unit.Repository.initialize(directory, name, uri)

    mock_os_makedirs.assert_called_with(os.path.join(directory, config.index_directory),
                                        exist_ok=True)
    mock_open.assert_called_with(os.path.join(directory, config.index_directory,
                                              config.index_file), mode='wb')


def test_init_repo_index_ok(mocker):
    """Assert index file contains the needed data."""
    directory = '/test'
    name = 'repositorytestname'
    uri = 'some:/uri/to/repo'
    index_data = {'display_name': name, 'uri': uri, 'configuration_version': config.version,
                  'index_file_name': config.index_file, 'sync_file_extension': config.extension}

    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('cntosync.file_sync.Repository.check_presence', return_value=False)
    mocker.patch('os.makedirs')
    mock_packb = mocker.patch('msgpack.packb')
    mock_open = mocker.patch('builtins.open')

    unit.Repository.initialize(directory, name, uri)

    mock_open.return_value.__enter__.return_value.write.assert_called()
    mock_packb.assert_called_once()
    assert mock_packb.call_args == call(index_data)


@pytest.mark.parametrize('overwrite', [
    True,
    False,
])
def test_init_repo_overwrite(overwrite, mocker):
    """Assert repository is re-initialized if overwrite enabled, assert not changed otherwise."""
    directory = '/test'
    name = ''
    uri = ''

    mocker.patch('cntosync.file_sync.Repository.check_presence', return_value=True)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('builtins.open')
    mock_makedirs = mocker.patch('os.makedirs')

    unit.Repository.initialize(directory, name, uri, overwrite)

    if not overwrite:
        mock_makedirs.assert_not_called()
    else:
        mock_makedirs.assert_called()


def test_init_repo_not_dir(mocker):
    """Assert directory is created if not existing."""
    directory = '/test'
    name = ''
    uri = ''

    mocker.patch('os.path.isdir', return_value=False)
    mock_makedirs = mocker.patch('os.makedirs')
    mocker.patch('cntosync.file_sync.Repository.check_presence', return_value=False)
    mocker.patch('builtins.open')

    unit.Repository.initialize(directory, name, uri)

    mock_makedirs.assert_any_call(directory, exist_ok=True)


def test_init_repo_permission_denied(mocker):
    """Assert error is raised if invalid permissions to create a directory."""
    directory = '/test'
    name = ''
    uri = ''

    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('os.makedirs', side_effect=PermissionError)
    mocker.patch('cntosync.file_sync.Repository.check_presence', return_value=False)
    mocker.patch('builtins.open')

    with pytest.raises(PermissionError):
        unit.Repository.initialize(directory, name, uri)
