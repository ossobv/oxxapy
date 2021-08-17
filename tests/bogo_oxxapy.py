# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from oxxapy import Oxxapy
from oxxapy.core import OxxapyRequest, OxxapyResponse
from oxxapy.exceptions import OxxapyTransportError


class _BogoOxxapy(Oxxapy):
    def __init__(self, *args, **kwargs):
        kwargs['username'] = kwargs.get('username', 'USER')
        md5pass = 'MD57a95bf926a0333f57705aeac07a362a2'  # md5('PASS')
        kwargs['password'] = kwargs.get('password', md5pass)
        super().__init__(*args, **kwargs)


class OxxapyBrokenHttp(_BogoOxxapy):
    """
    OXXA API bogus interface

    Reimplements _xml_call() so it returns an HTTP error.
    """
    def _xmlcall(self, command, **params):
        req = OxxapyRequest('https://BOGO-OXXAPY/command.php', command, params)
        raise OxxapyTransportError(
            503, 'Backend unavailable', req=req,
            binresp=b'<html>broken</html>')


class OxxapyWithResponse(_BogoOxxapy):
    """
    OXXA API bogus interface

    Reimplements _xml_call() so it returns previously pushed bogus answers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.__responses = []

    def push_reqresp(self, reqparams=None, binxml=None):
        """
        Push request and response that will be used instead of actually
        contacting the OXXA API.

        Example:

            api.push_reqresp(
                dict(command='domain_list', records=-1),
                b'''<channel><order><order_id>...</channel>''')
            api.domains.all()
        """
        assert isinstance(reqparams, dict), reqparams
        assert isinstance(binxml, bytes), binxml
        self.__responses.append((reqparams, binxml))

    def _xmlcall(self, command, **params):
        req = OxxapyRequest('https://BOGO-OXXAPY/command.php', command, params)
        reqparams, binxml = self.__responses.pop(0)
        assert req.params == reqparams, (req.params, reqparams)
        try:
            response = OxxapyResponse.from_binstr(binxml, req).extract_order()
        except Exception as e:
            raise OxxapyTransportError(
                200, str(e), req=req, binresp=binxml)
        return response
