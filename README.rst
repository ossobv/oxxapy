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
    for domain in api.domains.all():
        print(domain)

        if not domain.autorenew:
            domain.set_autorenew(True)

    # Get a domain directly:
    api.domains.get('example.com').set_autorenew(True)
    assert not api.domains.get('example.com').is_free()
