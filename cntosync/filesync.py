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
from typing import Dict, Iterable, List, Union
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

    def __init__(self, path: str,
                 index_filename: str = 'repoinfo', metafile_extension: str = '.cntosync') -> None:
        """Initialize object properties."""
        self.repo_path: str = os.path.abspath(path)

        self.index_subdir: str = configuration.index_directory
        self.index_fullpath: str = os.path.join(self.repo_path, self.index_subdir)
        self.index_filename: str = index_filename
        self.sync_file_ext: str = metafile_extension

        self.settings: Dict[str, Union[str, int]] = {}
        # Contains whole file checksums to quickly check if a file has been updated
        self.file_checksums: Dict[str, int] = {}
        # Contains the data required for the file syncronization
        self.file_sync_data: Dict = {}

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

    def index(self, flush: bool = False) -> None:
        """Generate main index file and sync files, update object status."""
        file_list = list_files(self.repo_path, [self.index_subdir, ], [self.sync_file_ext, ])
        gen_file_checksums = {}

        for file in file_list:
            gen_file_checksums[file] = file_checksum(file)
            if file not in self.file_checksums or self.file_checksums[file] != \
                    gen_file_checksums[file]:
                # File has been updated
                self.generate_file_sync_metadata(file)

        self.file_checksums = gen_file_checksums

        if flush:
            self.flush_index()
            self.flush_all_sync_files()

    def generate_file_sync_metadata(self, path: str) -> None:
        """Generate synchronisation metadata for file at `path`."""
        self.file_sync_data[path] = file_checksum(path)
        file_sync_path = path + self.sync_file_ext

    def flush_sync_file(self, file: str) -> None:
        """Write `file` synchronisation metadata into its synchronisation file."""
        sync_file_path = file + self.sync_file_ext

        with open(sync_file_path, mode='w+b') as sync_file:
            sync_file.write(msgpack.packb(self.file_sync_data[file]))

    def flush_all_sync_files(self) -> None:
        """Flush every synchronisation file."""
        for file in self.file_sync_data:
            self.flush_sync_file(file)

    def flush_index(self) -> None:
        """Update index file with current repository status, overwrite existing file."""
        index_content = {'settings': self.settings, 'whole_checksums': self.file_checksums}

        if not os.path.exists(self.index_fullpath):
            os.mkdir(self.index_fullpath)

        index_file_path = os.path.join(self.index_fullpath, self.index_filename)
        with open(index_file_path, mode='w+b') as index_file:
            index_file.write(msgpack.packb(index_content))
