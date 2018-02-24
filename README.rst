.. --------------------------------License Notice----------------------------------
.. CNTOSync - Carpe Noctem Tactical Operations ArmA3 mod synchronization tool
.. Copyright (C) 2018 Carpe Noctem - Tactical Operations (aka. CNTO) (contact@carpenoctem.co)
..
.. The authors of this software are listed in the AUTHORS file at the
.. root of this software's source code tree.
..
.. This program is free software: you can redistribute it and/or modify
.. it under the terms of the GNU General Public License as published by
.. the Free Software Foundation, either version 3 of the License, or
.. (at your option) any later version.
..
.. This program is distributed in the hope that it will be useful,
.. but WITHOUT ANY WARRANTY; without even the implied warranty of
.. MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
.. GNU General Public License for more details.
..
.. You should have received a copy of the GNU General Public License
.. along with this program.  If not, see <http://www.gnu.org/licenses/>.
.. All rights reserved.
.. --------------------------------License Notice----------------------------------

Carpe Noctem Tactical Operations ArmA3 mod synchronization tool
===============================================================

.. image:: https://travis-ci.org/CntoDev/CNTOSync.svg?branch=develop
    :target: https://travis-ci.org/CntoDev/CNTOSync
    :alt: Continuous Integration Build Status
.. image:: https://coveralls.io/repos/github/CntoDev/CNTOSync/badge.svg?branch=develop
    :target: https://coveralls.io/github/CntoDev/CNTOSync?branch=develop
    :alt: Code Coverage Status
.. image:: https://requires.io/github/CntoDev/CNTOSync/requirements.svg?branch=develop
    :target: https://requires.io/github/CntoDev/CNTOSync/requirements/?branch=develop
    :alt: Requirements Status

*CNTOSync* is an ArmA3 mod repository synchronization tool. This tool allows for members of an
ArmA3 community to download and keep updated a set of mods and addons against a central
HTTP-served repository.

*This software is currently under heavy development and is not ready to be used yet.*

Requirements
------------

* Python 3.6

Installation
------------

Assuming you are using a Python `virtualenv`, installation and upgrade of this software
can be achieved through the following command::

  pip install -U .

As using ``pip`` to install python packages directly in your Linux distribution's
system files is a **terrible idea**, system packages (RPM, DEB, AUR PKGBUILD, etc...) are
scheduled to be provided when the software reaches a more mature state. You are
encouraged to submit your OS-specific package files to the project to allow better
coverage.

Testing
-------

Install the package with the ``test`` extra selected, then start the ``tox`` tool::

  pip install -U -e '.[test]'
  tox

This will run the static analysis suite as well as the test suite.
