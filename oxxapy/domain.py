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

        <domain><!-- domain_list -->
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

        or

        <details><!-- domain_inf -->
          <identity-registrant>VQ0000000</identity-registrant>
          <identity-admin>VQ0000000</identity-admin>
          <identity-billing>MH0000000</identity-billing>
          <identity-tech>MH0000000</identity-tech>
          <identity-reseller>KULB12345</identity-reseller>
          <nsgroup>RG0000000</nsgroup>
          <expire_date>01-10-2021</expire_date>
          <notice_date>2021-10-01</notice_date>
          <autorenew>Y</autorenew>
          <usetrustee>N</usetrustee>
          <dnssec>Y</dnssec>
        </details>
        """
        name = xml_domain.get_str_value('domainname')
        ret = cls(core, name)
        ret._update_from_xml(xml_domain)
        return ret

    def __init__(self, core, name):
        name = name.lower()  # we compare against 'nl' below..
        self._core = core
        self._name = name
        self._sld, self._tld = name.split('.', 1)  # "co.uk" might be tld

        # > Deze informatie zal getoond worden als reseller in de
        # > WHOIS informatie van de SIDN (.NL).
        # So, for non-NL domains, we won't bother.
        if self._tld != 'nl':
            self._reseller = None

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
        self._expire_date = xml_domain.get_date_value('expire_date')

        # DNSSEC (only in domain_inf)
        try:
            self._dnssec = xml_domain.get_bool_value('dnssec')
        except OxxapyApplicationError:
            pass

        # Reseller values (only in domain_inf)
        # > Deze informatie zal getoond worden als reseller in de
        # > WHOIS informatie van de SIDN (.NL).
        # Don't bother for non-NL.
        if self._tld == 'nl':
            try:
                self._reseller = (
                    xml_domain.get_str_value('identity-reseller') or None)
            except OxxapyApplicationError:
                pass

    def _update(self):
        self._update_from_xml(self._call('domain_inf').get_child('details'))

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

    @property
    def reseller(self):
        if not hasattr(self, '_reseller'):
            self._update()
        return self._core.resellers.get(self._reseller)

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

    def set_reg_c(self, identity):
        "Change owner/reg_c/identity-registrant"
        raise NotImplementedError('''\
            Let op: een wijziging van de IDENTITY-REGISTRANT wordt
            opgevat als een domeinnaam overdracht naar een nieuwe
            houder. Afhankelijk van de domeinnaam extensie kan de
            registry hiervoor kosten in rekening brengen welke worden
            doorberekend.''')
        self._reg_c = self._set_identity('identity-registrant', identity)

    def set_c(self, admin_c=None, tech_c=None, bill_c=None):
        "Change admin_c + tech_c + bill_c at once"
        # It is sometimes needed to set multiple identities at once:
        # > Het domein bevat na deze update nog migratie profielen, je
        # > kan pas updaten wanneer alle migratie profielen zijn
        # > aangepast.
        #
        # If you attempt to set something to an already set handle, you'll get:
        # > <status_code>XMLERR 76</status_code>
        # > <status_description>
        # >   Domeinnaam reeds ingesteld met dit tech profiel
        # > </status_description>
        # So, don't do that.
        from .identity import OxxapyIdentity
        params = {}

        if admin_c is not None:
            assert isinstance(admin_c, OxxapyIdentity), (
                type(admin_c), admin_c)
            params['identity-admin'] = admin_c.handle

        if tech_c is not None:
            assert isinstance(tech_c, OxxapyIdentity), (
                type(tech_c), tech_c)
            params['identity-tech'] = tech_c.handle

        if bill_c is not None:
            assert isinstance(bill_c, OxxapyIdentity), (
                type(bill_c), bill_c)
            params['identity-billing'] = bill_c.handle

        if len(params) == 0:
            raise TypeError('set_c needs at least one argument')

        orderobj = self._call('domain_upd', **params)
        assert orderobj.status[0]

        if 'identity-admin' in params:
            self._admin_c = params['identity-admin']
        if 'identity-tech' in params:
            self._tech_c = params['identity-tech']
        if 'identity-billing' in params:
            self._bill_c = params['identity-billing']

    def _set_identity(self, field, identity):
        from .identity import OxxapyIdentity
        assert isinstance(identity, OxxapyIdentity), (type(identity), identity)
        orderobj = self._call('domain_upd', **{field: identity.handle})
        assert orderobj.status[0]
        return identity.handle

    def set_reseller(self, reseller):
        "Change or unset (None) reseller"
        from .reseller import OxxapyReseller
        if not isinstance(reseller, OxxapyReseller):
            raise TypeError('reseller must be OxxapyReseller type')
        if self._tld != 'nl':
            # <order>
            #   <order_id>123456789</order_id>
            #   <command>domain_upd</command>
            #   <sld>example</sld>
            #   <tld>com</tld>
            #   <status_code>XMLERR 53</status_code>
            #   <status_description>
            #     Er zijn geen nieuwe profielen opgegeven
            #   </status_description>
            #   <price>0</price>
            #   <order_complete>FALSE</order_complete>
            #   <done>TRUE</done>
            # </order>
            raise TypeError(
                'trying to set a reseller on a non-NL domain will fail')
        return self._call(
            'domain_upd', **{'identity-reseller': reseller.handle})


class OxxapyDomains(Manager):
    "Unbound domain manager"
    def __init__(self, core):
        self._core = core

    def get(self, domain):
        "Get a single bound domain"
        return OxxapyDomain(self._core, domain)

    def all(self):
        "Get all domains AS AN ITERABLE"
        return self.filter()

    def filter(
            self, domain=None, tld=None, nsgroup=None, identity=None,
            autorenew=None, lock=None, expire_date=None, status=None,
            status_days=None, reseller=None):
        "Get all domains that fit the filter expression AS AN ITERABLE"
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
            from .identity import OxxapyIdentity
            if not isinstance(identity, OxxapyIdentity):
                raise TypeError('identity must be OxxapyIdentity type')
            params['identity'] = identity.handle

        if autorenew is not None:
            assert autorenew in (True, False), autorenew
            params['autorenew'] = autorenew

        assert lock is None, NotImplemented
        assert expire_date is None, NotImplemented
        assert status is None, NotImplemented
        assert status_days is None, NotImplemented

        if reseller is not None:
            from .reseller import OxxapyReseller
            if not isinstance(reseller, OxxapyReseller):
                raise TypeError('reseller must be OxxapyReseller type')

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

        # Return domains as iterable so we get immediate results.
        for domain in ret:
            # If we have to do post-processing, that may take some addition
            # time.
            if reseller is not None and domain.reseller != reseller:
                continue
            yield domain
