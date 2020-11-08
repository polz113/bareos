#!/usr/bin/env python
#   BAREOS - Backup Archiving REcovery Open Sourced
#
#   Copyright (C) 2019-2020 Bareos GmbH & Co. KG
#
#   This program is Free Software; you can redistribute it and/or
#   modify it under the terms of version three of the GNU Affero General Public
#   License as published by the Free Software Foundation and included
#   in the file LICENSE.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#   Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#   02110-1301, USA.


# -*- coding: utf-8 -*-

from __future__ import print_function
import logging
import os
import unittest

import bareos.bsock
from bareos.bsock.protocolversions import ProtocolVersions
import bareos.exceptions


class PythonBareosBase(unittest.TestCase):
    director_address = "localhost"
    director_port = 9101
    director_extra_options = {}
    director_root_password = "secret"
    director_operator_username = "admin"
    director_operator_password = "secret"
    console_pam_username = u"PamConsole-notls"
    console_pam_password = u"secret"
    client = "bareos-fd"
    # restorefile = '/usr/sbin/bconsole'
    # path to store logging files
    backup_directory = "tmp/data/"
    debug = False
    logpath = "{}/PythonBareosTest.log".format(os.getcwd())

    def setUp(self):
        # Configure the logger, for information about the timings set it to INFO
        logging.basicConfig(
            filename=self.logpath,
            format="%(levelname)s %(module)s.%(funcName)s: %(message)s",
            level=logging.INFO,
        )
        logger = logging.getLogger()
        if self.debug:
            logger.setLevel(logging.DEBUG)
        logger.debug("setUp")

    def tearDown(self):
        logger = logging.getLogger()
        logger.debug("tearDown\n\n\n")

    def get_name_of_test(self):
        return self.id().split(".", 1)[1]


class PythonBareosPamLoginTest(PythonBareosBase):
    """
    Requires Bareos Console Protocol >= 18.2.
    """

    def test_pam_login_notls(self):

        pam_username = u"user1"
        pam_password = u"user1"

        #
        # login as console_pam_username
        #
        bareos_password = bareos.bsock.Password(self.console_pam_password)
        director = bareos.bsock.DirectorConsole(
            address=self.director_address,
            port=self.director_port,
            name=self.console_pam_username,
            password=bareos_password,
            pam_username=pam_username,
            pam_password=pam_password,
            **self.director_extra_options
        )

        whoami = director.call("whoami").decode("utf-8")
        self.assertEqual(pam_username, whoami.rstrip())

    @unittest.skipUnless(
        bareos.bsock.DirectorConsole.is_tls_psk_available(), "TLS-PSK is not available."
    )
    def test_pam_login_tls(self):

        pam_username = u"user1"
        pam_password = u"user1"

        console_pam_username = u"PamConsole"
        console_pam_password = u"secret"

        #
        # login as console_pam_username
        #
        bareos_password = bareos.bsock.Password(console_pam_password)
        director = bareos.bsock.DirectorConsole(
            address=self.director_address,
            port=self.director_port,
            name=console_pam_username,
            password=bareos_password,
            pam_username=pam_username,
            pam_password=pam_password,
            **self.director_extra_options
        )

        whoami = director.call("whoami").decode("utf-8")
        self.assertEqual(pam_username, whoami.rstrip())

    def test_pam_login_with_not_existing_username(self):
        """
        Verify bareos.bsock.DirectorConsole raises an AuthenticationError exception.
        """
        pam_username = "nonexistinguser"
        pam_password = "secret"

        bareos_password = bareos.bsock.Password(self.console_pam_password)
        with self.assertRaises(bareos.exceptions.AuthenticationError):
            director = bareos.bsock.DirectorConsole(
                address=self.director_address,
                port=self.director_port,
                name=self.console_pam_username,
                password=bareos_password,
                pam_username=pam_username,
                pam_password=pam_password,
                **self.director_extra_options
            )

    def test_login_with_not_wrong_password(self):
        """
        Verify bareos.bsock.DirectorConsole raises an AuthenticationError exception.
        """
        pam_username = "user1"
        pam_password = "WRONGPASSWORD"

        bareos_password = bareos.bsock.Password(self.console_pam_password)
        with self.assertRaises(bareos.exceptions.AuthenticationError):
            director = bareos.bsock.DirectorConsole(
                address=self.director_address,
                port=self.director_port,
                name=self.console_pam_username,
                password=bareos_password,
                pam_username=pam_username,
                pam_password=pam_password,
                **self.director_extra_options
            )

    def test_login_with_director_requires_pam_but_credentials_not_given(self):
        """
        When the Director tries to verify the PAM credentials,
        but no credentials where submitted,
        the login must fail.
        """

        bareos_password = bareos.bsock.Password(self.console_pam_password)
        with self.assertRaises(bareos.exceptions.AuthenticationError):
            director = bareos.bsock.DirectorConsole(
                address=self.director_address,
                port=self.director_port,
                name=self.console_pam_username,
                password=bareos_password,
                **self.director_extra_options
            )

    def test_login_without_director_pam_console_but_with_pam_credentials(self):
        """
        When PAM credentials are given,
        but the Director don't authenticate using them,
        the login should fail.
        """

        pam_username = u"user1"
        pam_password = u"user1"

        bareos_password = bareos.bsock.Password(self.director_operator_password)
        with self.assertRaises(bareos.exceptions.AuthenticationError):
            director = bareos.bsock.DirectorConsole(
                address=self.director_address,
                port=self.director_port,
                name=self.director_operator_username,
                password=bareos_password,
                pam_username=pam_username,
                pam_password=pam_password,
                **self.director_extra_options
            )

    def test_login_with_director_requires_pam_but_protocol_124(self):
        """
        When the Director tries to verify the PAM credentials,
        but the console connects via protocol bareos_12.4,
        the console first retrieves a "1000 OK",
        but further communication fails.
        In the end, a ConnectionLostError exception is raised.
        Sometimes this occurs during initialization,
        sometimes first the call command fails.
        """

        bareos_password = bareos.bsock.Password(self.console_pam_password)
        with self.assertRaises(bareos.exceptions.ConnectionLostError):
            director = bareos.bsock.DirectorConsole(
                address=self.director_address,
                port=self.director_port,
                protocolversion=ProtocolVersions.bareos_12_4,
                name=self.console_pam_username,
                password=bareos_password,
                **self.director_extra_options
            )
            result = director.call("whoami").decode("utf-8")


def get_env():
    """
    Get attributes as environment variables,
    if not available or set use defaults.
    """

    director_root_password = os.environ.get("dir_password")
    if director_root_password:
        PythonBareosBase.director_root_password = director_root_password

    director_port = os.environ.get("BAREOS_DIRECTOR_PORT")
    if director_port:
        PythonBareosBase.director_port = director_port

    backup_directory = os.environ.get("BackupDirectory")
    if backup_directory:
        PythonBareosBase.backup_directory = backup_directory

    tls_version_str = os.environ.get("PYTHON_BAREOS_TLS_VERSION")
    if tls_version_str is not None:
        tls_version_parser = bareos.bsock.TlsVersionParser()
        tls_version = tls_version_parser.get_protocol_version_from_string(
            tls_version_str
        )
        if tls_version is not None:
            PythonBareosBase.director_extra_options["tls_version"] = tls_version
        else:
            print(
                "Environment variable PYTHON_BAREOS_TLS_VERSION has invalid value ({}). Valid values: {}".format(
                    tls_version_str,
                    ", ".join(tls_version_parser.get_protocol_versions()),
                )
            )

    if os.environ.get("REGRESS_DEBUG"):
        PythonBareosBase.debug = True


if __name__ == "__main__":
    get_env()
    unittest.main()
