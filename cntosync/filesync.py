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
import zlib
from typing import Dict, Iterable, List, Sequence
from urllib.parse import urlparse

import msgpack

from . import configuration, exceptions


def valid_url(url: str) -> bool:
    """Check if string `url` is a valid URL compliant to RFC2396."""
    parsed_url = urlparse(url)

    return all([parsed_url.scheme, parsed_url.netloc])


def list_files(path: str, bl_subdirs: Iterable[str] = None, bl_extensions: Iterable[str] = None) \
        -> List:
    """List the absolute path to every file in a directory, subdirectories included."""
    if bl_subdirs is None:
        bl_subdirs = tuple()
    if bl_extensions is None:
        bl_extensions = tuple()

    dir_list = os.walk(path)
    file_list = []

    for dir_entry in dir_list:
        skip = False
        for bl_subdir in bl_subdirs:
            if bl_subdir in dir_entry[0].replace(path, ''):
                skip = True
        if skip:
            continue
        for file in dir_entry[2]:
            add = True
            for bl_extension in bl_extensions:
                if file.endswith(bl_extension):
                    add = False
            if add:
                file_list.append(dir_entry[0] + '/' + file)

    return file_list


def file_checksum(path: str) -> int:
    """Compute adler32 checksum of the whole content of a file."""
    with open(path, mode='rb') as file:
        checksum = zlib.adler32(file.read())

    return checksum


class Repository(object):
    """Wrap operations on a directory that contains a repository."""

    supported_url_schemas = ('file', 'http', 'https')

    def __init__(self, path: str, url: str = None, display_name: str = None) -> None:
        """Initialize object properties."""
        self.repo_path: str = os.path.abspath(path)
        self.url = url
        self.display_name = display_name

        self._index_subdir: str = configuration.index_directory
        self._index_path: str = os.path.join(self.repo_path, self._index_subdir)
        self._index_file_path: str = os.path.join(self._index_path, configuration.index_file)
        self._tree_file_path: str = os.path.join(self._index_path, configuration.tree_file)
        self._sync_file_extension: str = configuration.extension

        # Contains whole file checksums to quickly check if a file has been updated
        self.file_checksums: Dict[str, int] = {}

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

    # TODO: needs further documentation
    def build(self) -> None:
        """Update repository to reflect file changes."""
        updated_files: Sequence[str] = self._detect_updated_files()

        self._update_index_file()
        self._update_tree_file()
        for file in updated_files:
            self._update_synchronization_file(file)

    # TODO: improve/extend documentation
    def _detect_updated_files(self) -> Sequence[str]:
        """Return absolute paths of files that have been updated."""
        file_list = list_files(self.repo_path, [self._index_subdir, ], [self._sync_file_extension, ])
        updated_files: list = []

        for file in file_list:
            whole_file_checksum: int = file_checksum(file)
            if file not in self.file_checksums or whole_file_checksum != self.file_checksums[file]:
                updated_files.append(file)
                self.file_checksums[file] = whole_file_checksum

        return updated_files
    
    def _update_index_file(self) -> None:
        """Update repository index file to reflect object status."""
        pass

    def _update_tree_file(self) -> None:
        """Update repository tree file to reflect object status."""
        pass

    def _update_synchronization_file(self, file: str) -> None:
        """Update synchronization file `file` with object synchronization data."""
        pass


    # def generate_file_sync_metadata(self, path: str) -> None:
    #     """Generate synchronisation metadata for file at `path`."""
    #     self.file_sync_data[path] = file_checksum(path)
    #     file_sync_path = path + self.sync_file_ext

    # def flush_sync_file(self, file: str) -> None:
    #     """Write `file` synchronisation metadata into its synchronisation file."""
    #     sync_file_path = file + self.sync_file_ext

    #     with open(sync_file_path, mode='w+b') as sync_file:
    #         sync_file.write(msgpack.packb(self.file_sync_data[file]))

    # def flush_all_sync_files(self) -> None:
    #     """Flush every synchronisation file."""
    #     for file in self.file_sync_data:
    #         self.flush_sync_file(file)

    # def flush_index(self) -> None:
    #     """Update index file with current repository status, overwrite existing file."""
    #     index_content = {'settings': self.settings, 'whole_checksums': self.file_checksums}

    #     if not os.path.exists(self.index_fullpath):
    #         os.mkdir(self.index_fullpath)

    #     index_file_path = os.path.join(self.index_fullpath, self.index_filename)
    #     with open(index_file_path, mode='w+b') as index_file:
    #         index_file.write(msgpack.packb(index_content))
