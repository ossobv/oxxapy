# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from unittest import TestCase

from oxxapy.exceptions import (
    OxxapyTransportError,
    OxxapyTransactionError)
from oxxapy.response import OxxapyOrder

from bogo_oxxapy import OxxapyBrokenHttp, OxxapyWithResponse


class OxxapyTransportErrorTestCase(TestCase):
    def test_broken_http(self):
        api = OxxapyBrokenHttp()

        reqparams = dict(command='domain_list', records=-1)
        try:
            list(api.domains.all())
        except OxxapyTransportError as e:
            self.assertEqual(len(e.args), 4)
            self.assertEqual(e.args[0], 503)
            self.assertEqual(e.args[1], 'Backend unavailable'),
            self.assertTrue(e.args[2], reqparams)
            self.assertEqual(e.args[3], b'<html>broken</html>')
        else:
            raise AssertionError('OxxapyTransportError not raised')

    def test_broken_xml(self):
        api = OxxapyWithResponse()

        reqparams = dict(command='domain_list', records=-1)
        binxml = b'''\
<?xml version="1.0" encoding="UTF-8"?>
<channel>
  <order>
    <order_id>173714200</order_id><command>domain_list</command>
    <status_code>XMLOK18</status_code>
    <status_description>In DETAILS vind u de uitgebreide
      informatie</status_description>
    <price></price>
'''
        api.push_reqresp(reqparams, binxml)
        try:
            list(api.domains.all())
        except OxxapyTransportError as e:
            self.assertEqual(len(e.args), 4)
            self.assertEqual(e.args[0], 200)
            self.assertTrue(
                e.args[1].startswith('no element found'),
                e.args[1])
            self.assertTrue(e.args[2], reqparams)
            self.assertEqual(e.args[3], binxml)
        else:
            raise AssertionError('OxxapyTransportError not raised')


class OxxapyTransactionErrorTestCase(TestCase):
    def test_bad_status(self):
        api = OxxapyWithResponse()

        reqparams = dict(command='domain_inf', sld='example', tld='nl')
        binxml = b'''\
<?xml version="1.0" encoding="UTF-8"?>
<channel>
  <order>
    <order_id>173717176</order_id>
    <command>domain_inf</command>
    <sld>example</sld>
    <tld>nl</tld>
    <status_code>XMLERR 24</status_code>
    <status_description>Dit domein is niet onder beheer van deze
      gebruiker</status_description>
    <price>0</price>
    <order_complete>FALSE</order_complete>
    <done>TRUE</done>
  </order>
</channel>
'''
        api.push_reqresp(reqparams, binxml)
        try:
            api.domains.get('example.nl').nsgroup
        except OxxapyTransactionError as e:
            self.assertEqual(len(e.args), 4)
            self.assertEqual(e.args[0], 24)  # XMLERR 24
            self.assertTrue(
                e.args[1].startswith('Dit domein is niet onder beheer van'),
                e.args[1])
            self.assertTrue(e.args[2], reqparams)
            self.assertTrue(isinstance(e.args[3], OxxapyOrder), e.args[3])
        else:
            raise AssertionError('OxxapyTransactionError not raised')
