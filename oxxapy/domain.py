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
        name = xml_domain.get_str_value('domainname')
        ret = cls(core, name)
        ret._update_from_xml(xml_domain)
        return ret

    def __init__(self, core, name):
        self._core = core
        self._name = name
        self._sld, self._tld = name.split('.', 1)  # "co.uk" might be tld

    def __hash__(self):
        return hash(self._name)

    def __eq__(self, other):
        return self._name == other._name

    def __lt__(self, other):
        if self._name < other._name:
            return True
        return False

    def _update_from_xml(self, xml_domain):
        # IDs
        self._nsgroup = xml_domain.get_str_value('nsgroup')
        self._reg_c = xml_domain.get_str_value('identity-registrant')
        self._admin_c = xml_domain.get_str_value('identity-admin')
        self._tech_c = xml_domain.get_str_value('identity-tech')
        self._bill_c = xml_domain.get_str_value('identity-billing')
        # Renew
        self._autorenew = xml_domain.get_bool_value('autorenew')
        self._begin_date = xml_domain.get_date_value('start_date')
        self._end_date = xml_domain.get_date_value('expire_date')

    def _update(self):
        raise NotImplementedError()

    def _call(self, command, **params):
        return self._core._call(
            command, tld=self._tld, sld=self._sld, **params)

    def __repr__(self):
        return f'<OxxapyDomain({self._name})>'

    @property
    def name(self):
        return self._name

    @property
    def autorenew(self):
        if not hasattr(self, '_autorenew'):
            self._update()
        return self._autorenew

    @property
    def reg_c(self):
        if not hasattr(self, '_reg_c'):
            self._update()
        return self._core.identities.get(self._reg_c)

    @property
    def admin_c(self):
        if not hasattr(self, '_admin_c'):
            self._update()
        return self._core.identities.get(self._admin_c)

    @property
    def tech_c(self):
        if not hasattr(self, '_tech_c'):
            self._update()
        return self._core.identities.get(self._tech_c)

    @property
    def bill_c(self):
        if not hasattr(self, '_bill_c'):
            self._update()
        return self._core.identities.get(self._bill_c)

    @property
    def nsgroup(self):
        if not hasattr(self, '_nsgroup'):
            self._update()
        return self._core.nsgroups.get(self._nsgroup)

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
        params = {'records': -1}

        if domain is None and tld is not None:
            params['tld'] = tld
        elif domain is not None and tld is None:
            if '.' in domain:
                params['sld'], params['tld'] = domain.split('.', 1)
            else:
                params['sld'] = domain
        elif domain is not None and tld is not None:
            raise NotImplementedError('do not use both tld and domain')

        if nsgroup is not None:
            params['nsgroup'] = nsgroup
        if identity is not None:
            params['identity'] = identity

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
        details = resp.get_child('details')
        ret = []
        for domain in details.get_children('domain'):
            ret.append(OxxapyDomain.from_xml(self._core, domain))
        ret.sort()
        return ret
