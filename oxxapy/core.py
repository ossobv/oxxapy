# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from warnings import warn
from xml.etree import ElementTree

from .exceptions import (
    OxxapyTransportError, OxxapyTransactionError)


# url?apiuser=USER&apipassword=PASS&command=CMD[&test=Y]
API_URL = 'https://api.oxxa.com/command.php'


class _XmlResponse:
    def __init__(self, binstr, req):
        self._root = ElementTree.fromstring(binstr)
        self.orig_req = req

    def _parse(self):
        """
        Return inner <order/> from outer <channel/> as OxxapyOrder
        """
        if self._root.tag == 'channel':
            children = self._root.getchildren()
            if len(children) == 1 and children[0].tag == 'order':
                return OxxapyOrder(children[0], req=self.orig_req)
        raise NotImplementedError()

    def __str__(self):
        from xml.dom import minidom
        binstr = ElementTree.tostring(self._root)
        return minidom.parseString(binstr).toprettyxml(indent='  ')

    def __repr__(self):
        return '<_XmlResponse to="{}", """{}""">'.format(self.orig_req, self)

    @classmethod
    def _unmarshal_bool(cls, val):
        assert val in ('TRUE', 'FALSE'), val
        return val == 'TRUE'

    @classmethod
    def _unmarshal_bool_or_pending(cls, val):
        if val == 'PENDING':
            return None
        return cls._unmarshal_bool(val)


class OxxapyOrder(_XmlResponse):
    def __init__(self, root, req):
        self._root = root
        self.orig_req = req

        self.order_id = int(self._root.findtext('order_id'))
        self._status_code = self._root.findtext('status_code')
        self._status_description = self._root.findtext('status_description')
        self._order_complete = self._unmarshal_bool_or_pending(
            self._root.findtext('order_complete'))
        self.done = self._unmarshal_bool(self._root.findtext('done'))

    @property
    def status(self):
        """
        Get (success, status_int, status_message) tuple
        """
        if self._status_code.startswith('XMLOK'):
            return (
                True, int(self._status_code[5:].lstrip()),
                self._status_description)
        elif self._status_code.startswith('XMLERR'):
            return (
                False, int(self._status_code[6:].lstrip()),
                self._status_description)
        raise NotImplementedError(self._status_code)

    def is_order_complete(self, status):
        assert status in (False, True, None), status  # 'false, true, pending'
        return self._order_complete is status


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
                send_params[k] = ('Y' if v else 'N')
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
            response = _XmlResponse(data, req)._parse()
        except Exception as e:
            raise OxxapyTransportError(
                resp.status, str(e), req=req, binresp=data)
        return response
