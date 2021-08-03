# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from .exceptions import OxxapyApplicationError
from .manager import Manager


class OxxapyDomain:
    "Bound domain manager"
    def __init__(self, core, domain):
        self._core = core
        self._sld, self._tld = domain.split('.')

    def _call(self, command, **params):
        return self._core._call(
            command, tld=self._tld, sld=self._sld, **params)

    def is_free(self):
        "Return whether the domain is free (True) or not (False)"
        # > Met dit commando kan de beschikbaarheid van een domein
        # > worden gecontroleerd (vrij of bezet).
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


class OxxapyDomainManager(Manager):
    "Unbound domain manager"
    def __init__(self, core):
        self._core = core

    def __call__(self, domain):
        "Call the .domain property to get a bound domain"
        return OxxapyDomain(self._core, domain)

    def list(self):
        """
        blah blah
        """
        return self._core._call('domain_list')
