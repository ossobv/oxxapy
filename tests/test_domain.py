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

from bogo_oxxapy import OxxapyWithResponse


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

    def test_domain_all(self):
        api = OxxapyWithResponse()

        api.push_reqresp(
            dict(command='domain_list', records=-1),
            b'''\
<?xml version="1.0" encoding="UTF-8"?>
<channel>
  <order>
    <order_id>173714200</order_id><command>domain_list</command>
    <status_code>XMLOK18</status_code>
    <status_description>In DETAILS vind u de uitgebreide
      informatie</status_description>
    <price></price>
    <details>
      <domains_total>2</domains_total><domains_found>2</domains_found>
      <domain>
        <domainname>example.nl</domainname><nsgroup>NSGR00000</nsgroup>
        <identity-registrant>REGI00000</identity-registrant>
        <identity-admin>ADMI00000</identity-admin>
        <identity-tech>TECH00000</identity-tech>
        <identity-billing>BILL00000</identity-billing>
        <start_date>2013-11-26</start_date>
        <expire_date>2021-11-25</expire_date>
        <quarantaine_end></quarantaine_end>
        <notice_date>2021-11-25</notice_date><autorenew>Y</autorenew>
        <away_date></away_date>
        <last_renew_date>2020-11-11 00:17:22</last_renew_date>
        <lock>Y</lock><usetrustee>N</usetrustee>
      </domain>
      <domain>
        <domainname>example.com</domainname><nsgroup>NSGR00000</nsgroup>
        <identity-registrant>REGI00000</identity-registrant>
        <identity-admin>ADMI00000</identity-admin>
        <identity-tech>TECH00000</identity-tech>
        <identity-billing>BILL00000</identity-billing>
        <start_date>2013-11-26</start_date>
        <expire_date>2021-11-25</expire_date>
        <quarantaine_end></quarantaine_end>
        <notice_date>2021-11-25</notice_date><autorenew>Y</autorenew>
        <away_date></away_date>
        <last_renew_date>2020-11-11 00:17:22</last_renew_date>
        <lock>Y</lock><usetrustee>N</usetrustee>
      </domain>
    </details>
    <order_complete>TRUE</order_complete><done>TRUE</done>
  </order>
</channel>
''')

        domains = list(api.domains.all())
        self.assertEqual(len(domains), 2)

        # Sorted(!) so example.com goes first:
        example_com = domains[0]
        self.assertEqual(example_com.name, 'example.com')
        self.assertEqual(example_com.reg_c, api.identities.get('REGI00000'))
        self.assertEqual(example_com.admin_c, api.identities.get('ADMI00000'))
        self.assertEqual(example_com.tech_c, api.identities.get('TECH00000'))
        self.assertEqual(example_com.bill_c, api.identities.get('BILL00000'))
        self.assertEqual(example_com.reseller, api.resellers.none())
