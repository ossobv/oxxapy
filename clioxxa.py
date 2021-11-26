#!/usr/bin/env python3
# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
Sample CLI for OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

BEWARE: This script is subject to change. Its interface is NOT stable.
"""
import os
import sys

from oxxapy import Oxxapy


def transfer_domain(api, domain, transfer_key, registrant, admin, tech,
                    billing, reseller, nsgroup):
    cart_add_obj = api.raw(
        'cart_add', sld=domain._sld, tld=domain._tld,
        producttype='transfer',
        nsgroup=nsgroup.handle,
        trans_epp=transfer_key, **{
            'identity-registrant': registrant.handle,
            'identity-admin': admin.handle,
            'identity-tech': tech.handle,
            'identity-billing': billing.handle,
            'identity-reseller': reseller.handle,
        }
    )
    print(cart_add_obj)
    cart_id = cart_add_obj.get_int_value('details')

    # >>> api.raw('cart_list')
    # <OxxapyOrder to="{'command': 'cart_list'}", """<?xml version="1.0" ?>
    # <order>
    #   <order_id>123456789</order_id>
    #   <command>cart_list</command>
    #   <status_code>XMLOK 33</status_code>
    #   <status_description>Cart succesvol opgevraagd, uitgebreide informatie
    #     vind u in details</status_description>
    #   <price/>
    #   <details>
    #     <cartcount>1</cartcount>
    #     <totalcartcount>1</totalcartcount>
    #     <item>
    #       <itemid>123456</itemid>
    #       <producttype>register</producttype><!-- or 'transfer' -->
    #       <productdesc>example.com</productdesc>
    #       <currency>€</currency>
    #       <itemprice>0.92</itemprice>
    #       <totalprice>0.92</totalprice>
    #       <promotion>
    #         <conditions/>
    #         <start_date/>
    #         <end_date/>
    #         <normal>3.07</normal>
    #       </promotion>
    #       <price>
    #         <register>0.92</register><!-- or <transfer> -->
    #       </price>
    #       <quantity>1</quantity>
    #       <autorenew>Y</autorenew>
    #       <trustee>N</trustee>
    #       <lock/>
    #       <execution_at/>
    #       <expire_date_registry/>
    #       <configok>Y</configok>
    #       <messages>[]</messages>
    #       <configurable>Y</configurable>
    #       <type>quarterly</type>
    #       <childs/>
    #       <parent/>
    #     </item>
    #   </details>
    #   <order_complete>TRUE</order_complete>
    #   <done>TRUE</done>
    # </order>
    # """>

    # We can order the added item, or we can order all by using cart_id='ALL'.
    cart_purchase_obj = api.raw('cart_purchase', cart_id=cart_id)
    print(cart_purchase_obj)


def main():
    api = Oxxapy(os.environ['OXXAPY_USER'], os.environ['OXXAPY_PASS'])

    if sys.argv[1:] == ['id', 'ls']:
        for obj in sorted(api.identities.all(), key=(lambda x: x.alias)):
            print(obj.handle, '-', obj.alias)

    elif sys.argv[1:] == ['ns', 'ls']:
        for obj in sorted(api.nsgroups.all(), key=(lambda x: x.alias)):
            print(obj.handle, '-', obj.alias)

    elif sys.argv[1:] == ['rsl', 'ls']:
        for obj in sorted(api.resellers.all(), key=(lambda x: x.alias)):
            print(obj.handle, '-', obj.alias)

    elif sys.argv[1:2] == ['transfer']:
        assert len(sys.argv) == 10, (
            ('dom', 'key', 'regid', 'admid', 'techid', 'billid', 'rsl', 'ns'),
            sys.argv[2:])
        transfer_domain(
            api,
            domain=api.domains.get(sys.argv[2]),
            transfer_key=sys.argv[3],
            registrant=api.identities.get(sys.argv[4]),
            admin=api.identities.get(sys.argv[5]),
            tech=api.identities.get(sys.argv[6]),
            billing=api.identities.get(sys.argv[7]),
            reseller=api.resellers.get(sys.argv[8]),
            nsgroup=api.nsgroups.get(sys.argv[9]))

    else:
        print('List identities:  id ls')
        print('List nameservers: ns ls')
        print('List resellers:   rsl ls')
        print('Transfer:         transfer ...')
        print('Check the source for more help.')
        exit(1)


if __name__ == '__main__':
    main()
