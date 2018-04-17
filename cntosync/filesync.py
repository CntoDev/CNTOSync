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

"""Provide an interface for operations on a repository."""

import os
from urllib.parse import urlparse

import msgpack

from . import configuration
from . import exceptions


def valid_url(url: str) -> bool:
    """Check if string `url` is a valid URL compliant to RFC2396."""
    parsed_url = urlparse(url)

    return all([parsed_url.scheme, parsed_url.netloc])


class Repository(object):
    """Wrap operations on a directory that logically contains a repository."""

    supported_url_schemas = ('file', 'http', 'https')

    def __init__(self, directory: str) -> None:
        """Attempt to load existing repository configuration."""
        pass

    @staticmethod
    def check_presence(directory: str) -> bool:
        """Check if `directory` contains an initialized repository."""
        abs_directory = os.path.abspath(directory)
        index_subdirectory = os.path.join(abs_directory, configuration.index_directory)
        index_file_path = os.path.join(index_subdirectory, configuration.index_file)

        return all([
            os.path.isdir(abs_directory),
            os.path.isdir(index_subdirectory),
            os.path.isfile(index_file_path),
        ])

    @classmethod
    def initialize(cls, directory: str, display_name: str, url: str, overwrite: bool = False) \
            -> 'Repository':
        """Create new repository using `directory` as location."""
        if not valid_url(url):
            raise exceptions.InvalidURL('URL is not valid')
        parsed_url = urlparse(url)
        if parsed_url.scheme not in cls.supported_url_schemas:
            raise exceptions.UnsupportedURLSchema(cls.supported_url_schemas)

        path = os.path.abspath(directory)
        if not os.path.isdir(path):
            try:
                os.makedirs(path, exist_ok=True)
            except PermissionError:
                raise

        if cls.check_presence(directory) and not overwrite:
            return cls(directory)

        index_directory_path = os.path.join(directory, configuration.index_directory)
        os.makedirs(index_directory_path, exist_ok=True)

        index_file_path = os.path.join(index_directory_path, configuration.index_file)
        repository_index = {'display_name': display_name, 'url': url,
                            'configuration_version': configuration.version,
                            'index_file_name': configuration.index_file,
                            'sync_file_extension': configuration.extension}
        with open(index_file_path, mode='wb') as index_file:
            index_file.write(msgpack.packb(repository_index))

        return cls(directory)
