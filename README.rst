OXXA API in Python (oxxapy)
===========================

...more info...

Example usage
-------------

.. code-block:: python

    api = Oxxapy(os.environ['OXXAPY_USER'], os.environ['OXXAPY_PASS'])

    # Not preferred interface:
    orderobj = api.raw('domain_check', sld='example', tld='com')

    # Preferred interface:
    for dom in api.domains.filter(identity='VQHQ99548'):
        autorenew = 'Y' if dom.autorenew else 'N'
        print(
            f'{dom.name:32s}  {autorenew}  {dom.reg_c}  {dom.admin_c}'
            f'  {dom.tech_c}  {dom.bill_c}  {dom._nsgroup}')
        if not dom.autorenew:
            dom.set_autorenew(True)

    # Get a domain directly:
    api.domains.get('example.com').set_autorenew(True)
    assert not api.domains.get('example.com').is_free()
