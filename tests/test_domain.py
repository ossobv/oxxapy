# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from unittest import TestCase

from oxxapy.domain import OxxapyDomain

# Internals!
from oxxapy.response import ElementTree, _OxxapyXml



class OxxapyDomainTestCase(TestCase):
    def test_from_xml(self):
        for str_, bool_ in (('N', False), ('Y', True)):
            xml = _OxxapyXml(ElementTree.fromstring(f'''\
            <domain>
              <domainname>example.com</domainname>
              <nsgroup>RG0000000</nsgroup>
              <identity-registrant>VQ0000000</identity-registrant>
              <identity-admin>VQ0000000</identity-admin>
              <identity-tech>MH0000000</identity-tech>
              <identity-billing>MH0000000</identity-billing>
              <start_date>2021-04-01</start_date>
              <expire_date>2021-10-01</expire_date>
              <quarantaine_end/>
              <notice_date>2021-10-01</notice_date>
              <autorenew>{str_}</autorenew>
              <away_date/>
              <last_renew_date>2021-06-17 00:17:37</last_renew_date>
              <usetrustee>N</usetrustee>
            </domain>'''.encode('ascii')), req=None)

            core = None
            domain = OxxapyDomain.from_xml(core, xml)
            self.assertEqual(domain.autorenew, bool_)
