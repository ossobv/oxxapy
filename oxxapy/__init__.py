# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.

------------------------------------------------------------------------

https://www.oxxa.com/media/pdf/oxxa-api-v1.99.pdf

> De respons is geformatteerd in XML. Het is belangrijk dat u ieder
> commando test en uw code baseert op de daadwerkelijke reactie van de
> API.

> Alle invoer variabelen (behalve wachtwoorden) zijn niet
> hoofdlettergevoelig, maar houdt rekening met het feit dat de door u
> gehanteerde programmeertaal dit wel kan zijn. Parameters zelf dienen in
> kleine letters ingevoerd te worden. De voorbeelden in dit document zijn
> opgemaakt om prettig leesbaar te zijn en zijn niet maatgevend voor de
> daadwerkelijke reactie van de API.

> De invoer dient URL encoded te worden aangeleverd voor een goede
> verwerking van de gegevens. Eventuele vreemde tekens dienen in PUNY
> gecodeerd te zijn.

[...]

> Allereerst is de domeinnaam opgesplitst in twee gedeelten:
> - SLD (Second Level Domain)
> - TLD (Top Level Domain)
> In het voorbeeld example.org is ‘example’ de SLD en ‘org’ de TLD.

> [...] bij elke verhuizing dienen [Registrant_identity, Admin_identity,
> Billing_identity en Tech_identity] opgegeven worden door het aanwijzen
> van bestaande contact profielen (identities).

Example API call response:

  <?xml version="1.0" encoding="ISO-8859-1" ?>
  <channel>
    <order>
      <order_id>1234567</order_id>
      <command>domain_list</command>
      <status_code>XMLOK18</status_code>
      <status_description>In DETAILS vindt u ...</status_description>
      <price>0.00</price>
      <details>
        <domains_total>1</domains_total>
        <domains_found>1</domains_found>
        <domain>
          <domainname>example.org</domainname>
          <nsgroup>ABCD123456</nsgroup>
          <start_date>2009-04-08</start_date>
          <expire_date>2010-04-08</expire_date>
          <autorenew>Y</autorenew>
          <lock>Y</lock>
        </domain>
      </details>
      <order_complete>TRUE</order_complete><!-- TRUE, PENDING or FALSE -->
      <done>TRUE</done><!-- means "end of output" -->
    </order>
  </channel>

------------------------------------------------------------------------

Preferred API call syntax:

  api = TheApi(...)

  api.direct('domain_check', sld='example', tld='com')

  api.domain.list()
  api.domain('example.com').autorenew(True)
  api.domain('example.com').info()

"""
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from warnings import warn
from xml.etree import ElementTree


# url?apiuser=USER&apipassword=PASS&command=CMD[&test=Y]
API_URL = 'https://api.oxxa.com/command.php'


class OxxapyError(Exception):
    pass


class OxxapyTransportError(OxxapyError):
    "No or bad API response"
    def __init__(self, http_status, message, req, binresp):
        super().__init__(http_status, message, req, binresp)


class OxxapyTransactionError(OxxapyError):
    "Negative API response"
    def __init__(self, xmlerr_status, message, req, resp):
        super().__init__(xmlerr_status, message, req, resp)


class OxxapyApplicationError(OxxapyError):
    "API abstraction error"
    def __init__(self, xmlok_status, message, req, resp):
        super().__init__(xmlok_status, message, req, resp)


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


class Manager:
    """
    Inherit from this when you're creating a property on the OxxapyCore,
    like this:

        class Domain(Manager):
            class DomainSel:
                def __init__(self, core, domain):
                    self._core = core
                    self._domain = domain

                def do_something_with_domain(self):
                    pass

            def __call__(self, domain):
                return self.DomainSel(self._core, domain)

            def list(self):
                pass

        class Oxxapy(...):
            domain = Domain.as_property()

        api = Oxxapy(...)
        api.domain.list()
        api.domain('example.com').do_something_with_domain()
    """
    @classmethod
    def as_property(cls):
        @property
        def cached_getter(core):
            propname = '_prop_%s' % (cls.__name__,)
            if not hasattr(core, propname):
                setattr(core, propname, cls(core))
            return getattr(core, propname)

        return cached_getter

    def __init__(self, core):
        self._core = core


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


class OxxapyDomain(Manager):
    class OxxapyDomainSelected:
        def __init__(self, core, domain):
            self._core = core
            self._sld, self._tld = domain.split('.')

        def _call(self, command, **params):
            return self._core._call(
                command, tld=self._tld, sld=self._sld, **params)

        def is_free(self):
            """
            Met dit commando kan de beschikbaarheid van een domein
            worden gecontroleerd (vrij of bezet).
            """
            resp = self._call('domain_check')
            if resp.status[1] == 10:
                return False
            elif resp.status[1] == 11:
                return True
            raise OxxapyApplicationError(
                resp.status[1], 'unspected status code', req=resp.orig_req,
                resp=resp)

        def set_autorenew(self, boolean):
            "Set/change auto renew status"  # (idempotent)
            assert boolean in (True, False), boolean
            # > Met dit commando kan worden bepaald of een domeinnaam
            # > automatisch 30 dagen voor de afloopdatum automatisch door
            # > het systeem wordt verlengd.
            return self._call('autorenew', autorenew=boolean)

#         def epp(self, send_email):
#             """
#             Dit commando zendt de EPP code van een domein per email aan
#             de registrant. In het veld details kunt u bij een aantal TLD
#             gelijk de verhuiscode inzien. Dit is helaas niet mogelijk
#             bij alle TLD’s en daarom worden deze per email verzonden.
#             """
#             assert send_email is True, 'this command will send an email'
#             return self._call('epp')
#
#         def info(self):
#             """
#             Dit commando geeft de actuele configuratie van een
#             domeinnaam registratie. Relevant zijn: NSGROUP, IDENTITIES,
#             EXPIRE_DATE,AUTORENEW,LOCK
#             """
#             return self._call('domain_inf')
#
#         def quarantine(self):
#             """
#             Dit commando plaatst een domein onmiddellijk in quarantaine.
#             """
#             # return self._call('domain_del')
#             raise NotImplementedError(
#                 'use autorenew(False) instead; '
#                 'this would place the domain in immediate quarantine')
#
#         def unquarantine(self):
#             """
#             Dit commando [herstelt] een domeinnaam uit quarantaine.
#             """
#             return self._call('domain_restore')

    def __init__(self, core):
        self._core = core

    def __call__(self, domain):
        return self.OxxapyDomainSelected(self._core, domain)

    def list(self):
        """
        blah blah
        """
        return self._core._call('domain_list')


class Oxxapy(OxxapyCore):
    domain = OxxapyDomain.as_property()


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
