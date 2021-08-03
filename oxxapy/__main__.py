# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from . import Oxxapy


if __name__ == '__main__':
    import os
    api = Oxxapy(os.environ['OXXAPY_USER'], os.environ['OXXAPY_PASS'])

    resp = api.domain.list()  # equals: api._call('domain_list')
    print(resp)

    if api.domain('this-is-still-free.com').is_free():
        print('domain is free for the taking')
    else:
        print('domain is already taken')

    # print(api.domain('example.com').autorenew(False))
    # import pdb; pdb.set_trace()
