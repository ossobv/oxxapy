# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from datetime import date
from unittest import TestCase

from oxxapy.exceptions import OxxapyApplicationError
from oxxapy.response import ElementTree, _OxxapyXml


class OxxapyXmlTestCase(TestCase):
    def test_date_fail(self):
        xml = _OxxapyXml(ElementTree.fromstring(f'''\
        <domain>
          <start_date>2021</start_date>
          <expire_date>2021</expire_date>
        </domain>'''.encode('ascii')), req=None)
        self.assertRaises(
            OxxapyApplicationError, xml.get_date_value, 'missing_field')
        self.assertRaises(
            OxxapyApplicationError, xml.get_date_value, 'start_date')

    def test_date_ymd(self):
        xml = _OxxapyXml(ElementTree.fromstring(f'''\
        <domain>
          <start_date>2021-04-01</start_date>
          <expire_date>2021-10-01</expire_date>
        </domain>'''.encode('ascii')), req=None)
        self.assertEqual(
            xml.get_date_value('start_date'), date(2021, 4, 1))

    def test_date_dmy(self):
        xml = _OxxapyXml(ElementTree.fromstring(f'''\
        <domain>
          <start_date>01-04-2021</start_date>
          <expire_date>01-10-2021</expire_date>
        </domain>'''.encode('ascii')), req=None)
        self.assertEqual(
            xml.get_date_value('start_date'), date(2021, 4, 1))
