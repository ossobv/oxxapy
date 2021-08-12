OXXA API in Python (oxxapy)
===========================

...more info...

Example usage
-------------

Creating an API instance:

.. code-block:: python

    import os
    from oxxapy import Oxxapy

    api = Oxxapy(os.environ['OXXAPY_USER'], os.environ['OXXAPY_PASS'])

Low level interface:

.. code-block:: python

    # Not preferred interface, but available for API calls that do not
    # have a higher level interface.
    orderobj = api.raw('domain_check', sld='example', tld='com')
    print(orderobj)
    # <OxxapyOrder to="{
    #   'sld': 'example', 'tld': 'com', 'command': 'domain_check'}",
    #   """<?xml version="1.0" ?>
    # <order>
    #   <order_id>123457890</order_id>
    #   <command>domain_check</command>
    #   <sld>example</sld>
    #   <tld>com</tld>
    #   <status_code>XMLOK 10</status_code>
    #   <status_description>Domeinnaam is bezet.</status_description>
    #   <price/>
    #   <details>
    #     <cart>N</cart>
    #     <managed>Y</managed>
    #     <price>0.92</price>
    #     <normal>3.07</normal>
    #     <currency>&amp;euro;</currency>
    #     <currency2>EUR</currency2>
    #     <type>quarterly</type>
    #     <start_date>11-08-2021</start_date>
    #     <end_date>11-08-2021</end_date>
    #     <conditions/>
    #   </details>
    #   <order_complete>TRUE</order_complete>
    #   <done>TRUE</done>
    # </order>
    orderdetails = orderobj.get_child('details')
    assert orderdetails.get_str_value('currency2') == 'EUR'
    assert orderdetails.get_date_value('end_date') == date(2021, 8, 11)

    # Looking at and updating an identity:
    orderobj = api.raw('identity_get', identity='VQHQ99548')
    print(orderobj)
    orderobj = api.raw('identity_upd', identity='VQHQ99548', street='Sesame')
    print(orderobj)
    orderobj = api.raw('identity_get', identity='VQHQ99548')
    print(orderobj)

Higher level interface, preferred:

.. code-block:: python

    # Looping over filtered/searched results:
    # BEWARE: domains.filter()/all() returns an iterable!
    for dom in api.domains.filter(identity='VQHQ99548'):
        autorenew = 'Y' if dom.autorenew else 'N'
        print(
            f'{dom.name:32s}  {autorenew}  {dom.reg_c}  {dom.admin_c}'
            f'  {dom.tech_c}  {dom.bill_c}  {dom._nsgroup}')

        # Set domain to autorenew if it wasn't already:
        if not dom.autorenew:
            dom.set_autorenew(True)

    # You can also act on (unfetched) domains directly:
    api.domains.get('example.com').set_autorenew(True)
    assert not api.domains.get('example.com').is_free()

And, how about listing all domains per owner:

.. code-block:: python

    # Prefetch identities:
    api.identities.all()

    # Get all domains that have autorenew enabled:
    # BEWARE: domains.filter()/all() returns an iterable!
    domains = api.domains.filter(autorenew=True)

    # Sort them by reg-c:
    domains_by_regcs = defaultdict(list)
    for domain in domains:
        domains_by_regcs[domain.reg_c].append(domain)

    # Print them in groups:
    for regc, domains in domains_by_regcs.items():
        print(regc._alias, ' #', regc.handle)
        for domain in domains:
            print('-', domain.name)
        print()
    # ACME Inc  # HNDL1234
    # - example.com
    # - example.org

And, fixing migration identities:

.. code-block:: python

    # Check and set bill_c on all domains to a single bill_c (MHFQ12345),
    # and make reg_c and admin_c equal:
    osso_c = api.identities.get('MHFQ12345')
    for domain in domains:
        if domain.reg_c != domain.admin_c or (
                domain.tech_c != osso_c or domain.bill_c != osso_c):
            print(
                '1>', domain.reg_c, domain.admin_c,
                domain.tech_c, domain.bill_c, domain)

            # First, we must fix any migration profiles:
            params = {}
            if domain.admin_c.handle == 'IDEN12345':
                params['admin_c'] = domain.reg_c
            if domain.tech_c.handle == 'IDEN12345':
                params['tech_c'] = osso_c
            if domain.bill_c.handle == 'IDEN12345':
                params['bill_c'] = osso_c

            if params:
                domain.set_c(**params)
                print('updated *_c', domain, params)

            # Secondly, we can update individual fields if needed:
            # admin_c <== reg_c
            if not (domain.reg_c == domain.admin_c):
                domain.set_c(admin_c=domain.reg_c)
            # tech_c <== osso_c
            if not (domain.tech_c == osso_c):
                domain.set_c(tech_c=osso_c)
            # bill_c <== osso_c
            if not (domain.bill_c == osso_c):
                domain.set_c(bill_c=osso_c)

            print(
                '2>', domain.reg_c, domain.admin_c,
                domain.tech_c, domain.bill_c, domain)

Setting all NL domains that have no reseller to our only reseller:

.. code-block:: python

    resellers = api.resellers.all()
    for reseller in resellers:
        print(reseller)
    # reseller now holds last (and only relevant) reseller (to us)

    no_reseller = api.resellers.none()  # the special NONE-reseller
    domains = api.domains.filter(
        reseller=no_reseller, autorenew=True, tld='nl')
    for domain in domains:
        assert domain.reseller == no_reseller, domain.reseller
        print(domain, 'setting reseller to', reseller)
        domain.set_reseller(reseller)

Unsetting a reseller profile from an NL-domain:

.. code-block:: python

    domain = api.domains.get('example.nl')
    domain.set_reseller(api.resellers.none())
