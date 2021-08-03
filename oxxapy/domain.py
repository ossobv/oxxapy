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
    @classmethod
    def from_xml(cls, core, xml_domain):
        """
        Turn _OxxapyXml into domain with prefilled values

        <domain>
          <domainname>example.com</domainname>
          <nsgroup>RG0000000</nsgroup>
          <identity-registrant>VQ0000000</identity-registrant>
          <identity-admin>VQ0000000</identity-admin>
          <identity-tech>MH0000000</identity-tech>
          <identity-billing>MH0000000</identity-billing>
          <start_date>2021-04-01</start_date>
          <expire_date>2021-10-01</expire_date>
          <quarantaine_end/>
          <notice_date>2021-10-01</notice_date>
          <autorenew>Y</autorenew>
          <away_date/>
          <last_renew_date>2021-06-17 00:17:37</last_renew_date>
          <usetrustee>N</usetrustee>
        </domain>
        """
        domain = xml_domain.get_str_value('domainname')
        ret = cls(core, domain)
        ret._autorenew = xml_domain.get_bool_value('autorenew')
        # FIXME: extract more..
        return ret

    def __init__(self, core, domain):
        self._core = core
        self._domain = domain
        self._sld, self._tld = domain.split('.', 1)  # "co.uk" might be tld

    def _call(self, command, **params):
        return self._core._call(
            command, tld=self._tld, sld=self._sld, **params)

    def __repr__(self):
        return f'<OxxapyDomain({self._domain})>'

    @property
    def autorenew(self):
        # FIXME: if not set, then fetch
        return self._autorenew

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


class OxxapyDomains(Manager):
    "Unbound domain manager"
    def __init__(self, core):
        self._core = core

    def get(self, domain):
        "Get a single bound domain"
        return OxxapyDomain(self._core, domain)

    def all(self):
        "Get all domains"
        return self.filter()

    def filter(
            self, domain=None, tld=None, nsgroup=None, identity=None,
            autorenew=None, lock=None, expire_date=None, status=None,
            status_days=None):
        "Get all domains that fit the filter expression"
        params = {}

        if domain is None and tld is not None:
            params['tld'] = tld
        elif domain is not None and tld is None:
            if '.' in domain:
                params['sld'], params['tld'] = domain.split('.', 1)
            else:
                params['sld'] = domain
        elif domain is not None and tld is not None:
            raise NotImplementedError('do not use both tld and domain')

        assert nsgroup is None, NotImplemented
        assert identity is None, NotImplemented

        if autorenew is not None:
            assert autorenew in (True, False), autorenew
            params['autorenew'] = autorenew

        assert lock is None, NotImplemented
        assert expire_date is None, NotImplemented
        assert status is None, NotImplemented
        assert status_days is None, NotImplemented

        # Variabelen:
        # - START (optioneel) Startveld van de lijstweergave (standaard = 0)
        # > - RECORDS (optioneel) Maximaal te tonen records in
        # >   lijstweergave (standaard = 25, bij een waarde van -1 wordt
        # >   de volledige lijst getoond)
        # > - SORTNAME (optioneel) Veld waarop de lijstweergave
        # >   gesorteerd wordt
        # > - SORTORDER (optioneel) Sorteervolgorde aflopend of oplopend
        # >   (ASC / DESC)
        # > - SLD (optioneel) Zoekvoorwaarde voor de SLD
        # > - TLD (optioneel) Zoekvoorwaarde voor de TLD
        # > - NSGROUP (optioneel) Zoekvoorwaarde voor de nsgroup
        # > - IDENTITY (optioneel) Zoekvoorwaarde voor een van de identities
        # > - AUTORENEW (optioneel) Zoekvoorwaarde voor de autorenew
        # > - LOCK (optioneel) Zoekvoorwaarde voor de lock
        # > - EXPIRE_DATE (optioneel) Zoekvoorwaarde voor de expire_date
        # > - STATUS (optioneel) Zoekvoorwaarde voor status:
        # >   o Active Alle actieve domeinnamen
        # >   o Quarantaine Alle domeinnamen in quarantaine
        # >   o Delete Alle verwijderde domeinnamen
        # >   o Inactive Alle in-actieve domeinnamen
        # >   o Transferd Alle wegverhuisde domeinnamen (te combineren
        # >     met DAYS)
        # >   o Expired Alle verlopen domeinnamen (te combineren met DAYS)
        # >   o Renewed Alle verlengde domeinnamen (te combineren met DAYS)
        # >   o Renew Alle aankomende verlengingen (te combineren met DAYS)
        # > - DAYS (optioneel) Zoekwaarde die te combineren is met
        # >   status parameters.
        resp = self._core._call('domain_list', **params)
        domains = resp.get_children('domains')[0]
        # XXX: broken
        return resp
