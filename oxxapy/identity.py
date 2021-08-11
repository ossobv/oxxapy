# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from .manager import Manager


class OxxapyIdentity:
    "Bound identity manager"
    @classmethod
    def from_xml(cls, core, xml_handle):
        """
        Turn _OxxapyXml into identity with prefilled values

        <identity>
          <handle>SQGU88967</handle>
          <alias>ACME Inc</alias>
          <company_name>ACME Inc</company_name>
          <name>Doe, John</name>
        </identity>
        """
        handle = xml_handle.get_str_value('handle')
        ret = cls(core, handle)
        ret._update_from_xml(xml_handle)
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

    def _update_from_xml(self, xml_handle):
        # FIXME: more fields..
        self._alias = xml_handle.get_str_value('alias')

        lastname_firstname = xml_handle.get_str_value('name')
        if ', ' in lastname_firstname:
            self._lastname, self._firstname = lastname_firstname.split(
                ', ', 1)
        else:
            self._lastname, self._firstname = lastname_firstname, ''

        self._company_name = xml_handle.get_str_value('company_name')

    def _update(self):
        raise NotImplementedError()

    def __repr__(self):
        return f'<OxxapyIdentity({self._handle})>'

    @property
    def handle(self):
        return self._handle

    @property
    def nameaddr(self):
        return '{} {} <{}>'.format(
            self._firstname, self._lastname, self._email)


class OxxapyIdentities(Manager):
    "Unbound identity manager"
    def __init__(self, core):
        self._core = core

    def get(self, handle):
        "Get a single bound identity"
        return self._core._cache_get(
            OxxapyIdentity, handle, (lambda: (
                OxxapyIdentity(self._core, handle))))

    def all(self):
        "Get all identities"
        return self.filter()

    def filter(
            self, handle=None, name=None, company_name=None, alias=None,
            global_search=None):
        "Get all identities that fit the filter expression"
        params = {'records': -1}

        assert handle is None, NotImplemented
        assert name is None, NotImplemented
        assert company_name is None, NotImplemented
        assert alias is None, NotImplemented
        assert global_search is None, NotImplemented

        # > Variabelen:
        # > - HANDLE (optioneel) Zoekwaarde voor de identity handle.
        # > - NAME (optioneel) Zoekwaarde voor de naam.
        # > - COMPANY_NAME (optioneel) Zoekwaarde voor bedrijfsnaam.
        # > - ALIAS (optioneel) Zoekwaarde voor de alias.
        # > - SORTNAME (optioneel) Veld waarop gesorteerd moet worden.
        # > - SORTORDER (optioneel) Sorteervolgorde (ASC of DESC).
        # > - GLOBAL_SEARCH (optioneel) Zoekwaarde voor alle velden.
        # > - START (optioneel) Bij welk veld moet worden begonnen met weergave
        # >   (standaard: 0).
        # > - RECORDS (optioneel) Hoeveel records moeten er worden weergegeven
        # >   (standaard: 25, -1 is alles).
        resp = self._core._call('identity_list', **params)
        details = resp.get_child('details')
        ret = []

        self._core._cache_clear(OxxapyIdentity)
        for xml_identity in details.get_children('identity'):
            identity = OxxapyIdentity.from_xml(self._core, xml_identity)
            self._core._cache_set(OxxapyIdentity, identity.handle, identity)
            ret.append(identity)

        ret.sort()
        return ret
