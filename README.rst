OXXA API in Python (oxxapy)
===========================

...more info...

Example usage
-------------

.. code-block:: python

    api = Oxxapy(os.environ['OXXAPY_USER'], os.environ['OXXAPY_PASS'])

    api.domain.list()

    api.domain('example.com').check()
    api.domain('example.com').autorenew(True)
