# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from .manager import Manager


class OxxapyNsgroup:
    "Bound nameservergroup manager"
    @classmethod
    def from_xml(cls, core, xml_nsgroup):
        """
        Turn _OxxapyXml into nameservergroup with prefilled values

        <nsgroup>
          <handle>YDNR00000</handle>
          <alias>Managed DNS service</alias>
          <nameservers>
            <ns1_fqdn>ns1.thednscompany.com</ns1_fqdn>
            <ns2_fqdn>ns2.thednscompany.com</ns2_fqdn>
            <ns3_fqdn>ns3.thednscompany.com</ns3_fqdn>
          </nameservers>
        </nsgroup>
        """
        handle = xml_nsgroup.get_str_value('handle')
        ret = cls(core, handle)
        ret._update_from_xml(xml_nsgroup)
        return ret

    def __init__(self, core, handle):
        self._core = core
        self._handle = handle

    def __hash__(self):
        return hash(self._handle)

    def __eq__(self, other):
        return self._handle == other._handle

    def __lt__(self, other):
        if self._handle < other._handle:
            return True
        return False

    def _update_from_xml(self, xml_nsgroup):
        self._alias = xml_nsgroup.get_str_value('alias')

    def _update(self):
        raise NotImplementedError()

    def __repr__(self):
        return f'<OxxapyNsgroup({self._handle})>'

    @property
    def handle(self):
        return self._handle


class OxxapyNsgroups(Manager):
    "Unbound nameservergroup manager"
    def __init__(self, core):
        self._core = core

    def get(self, handle):
        "Get a single bound nameservergroup"
        return self._core._cache_get(
            OxxapyNsgroup, handle, (lambda: OxxapyNsgroup(self._core, handle)))

    def all(self):
        "Get all nameservergroups"
        return self.filter()

    def filter(self, handle=None, global_search=None, alias=None):
        "Get all nameservergroups that fit the filter expression"
        params = {'records': -1}

        assert handle is None, NotImplemented
        assert global_search is None, NotImplemented
        assert alias is None, NotImplemented

        # > Variabelen:
        # > - SORTNAME (optioneel) Veld waarop gesorteerd moet worden.
        # > - SORTORDER (optioneel) Sorteervolgorde (ASC of DESC).
        # > - NSGROUP (optioneel) Zoekwaarde voor de nsgroup handle.
        # > - GLOBAL_SEARCH (optioneel) Zoekwaarde voor alle velden.
        # > - ALIAS (optioneel) Zoekwaarde voor de naam.
        # > - START (optioneel) Bij welk veld moet worden begonnen met
        # >   weergave (standaard: 0).
        # > - RECORDS (optioneel) Hoeveel records moeten er worden weergegeven
        # >   (standaard: 25, -1 is alles).
        resp = self._core._call('nsgroup_list', **params)
        details = resp.get_child('details')
        ret = []

        self._core._cache_clear(OxxapyNsgroup)
        for xml_nsgroup in details.get_children('nsgroup'):
            nsgroup = OxxapyNsgroup.from_xml(self._core, xml_nsgroup)
            self._core._cache_set(OxxapyNsgroup, nsgroup.handle, nsgroup)
            ret.append(nsgroup)

        ret.sort()
        return ret
