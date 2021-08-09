# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from warnings import warn

from .exceptions import (
    OxxapyTransportError, OxxapyTransactionError)
from .response import OxxapyResponse


# url?apiuser=USER&apipassword=PASS&command=CMD[&test=Y]
API_URL = 'https://api.oxxa.com/command.php'


class OxxapyRequest:
    def __init__(self, url, command, params={}):
        self.url = url
        self.params = params.copy()
        self.params.update({'command': command})

    def get_urllib_request(self, extra_params):
        send_params = self.params.copy()
        send_params.update(extra_params)
        for k, v in send_params.items():
            if isinstance(v, str):
                pass
            elif isinstance(v, bool):
                # FIXME: this may be problematic if other fields are boolean
                # but want a TRUE/FALSE instead..
                send_params[k] = ('Y' if v else 'N')
            elif isinstance(v, int):
                send_params[k] = str(v)
            else:
                assert False, f'unexpected non-string {k}={v}'
        send_params = dict(
            (k.encode('ascii'), v.encode('ascii'))
            for k, v in send_params.items())

        headers = {
            'User-Agent': 'Oxxapy-0.0',
        }

        # Don't use Request(data=send_params), but urlencode it ourself.
        url = f'{self.url}?{urlencode(send_params)}'
        if False:
            print(f'>>> {url}')
        return Request(url=url, headers=headers, method='GET')

    def __repr__(self):
        return repr(self.params)


class OxxapyCore:
    def __init__(self, username, password):
        assert len(username)
        assert len(password)

        if not (password.startswith('MD5') and len(password) == (32 + 3)):
            from hashlib import md5
            warn("Prefer password='MD5'+md5('password').hexdigest()")
            password = 'MD5{}'.format(
                md5(password.encode('ascii')).hexdigest())

        self._apiurl = API_URL
        self._username, self._password = username, password

    def _call(self, command, **params):
        resp = self._xmlcall(command, **params)
        status_ok, status_code, status_msg = resp.status
        if not status_ok:
            raise OxxapyTransactionError(
                status_code, status_msg, req=resp.orig_req, resp=resp)
        return resp

    def _xmlcall(self, command, **params):
        req = OxxapyRequest(self._apiurl, command, params)
        resp = urlopen(req.get_urllib_request(
            {'apiuser': self._username, 'apipassword': self._password}))
        try:
            data = resp.read()
        except Exception as e:
            data = b''
            raise OxxapyTransportError(
                resp.status, str(e), req=req, binresp=data)
        if resp.status != 200:
            raise OxxapyTransportError(
                resp.status, resp.reason, req=req, binresp=data)
        try:
            response = OxxapyResponse.from_binstr(data, req).extract_order()
        except Exception as e:
            raise OxxapyTransportError(
                resp.status, str(e), req=req, binresp=data)
        return response
