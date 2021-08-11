# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from .manager import Manager


class OxxapyReseller:
    "Bound reseller manager"
    @classmethod
    def from_xml(cls, core, xml_reseller):
        """
        Turn _OxxapyXml into reseller with prefilled values

        <identity>
          <handle>KULB12345</handle>
          <alias>ACME Registrar</alias>
          <company>ACME Inc</company>
        </identity>

        NOTE: Contrary to what the v1.99 API docs say, we do NOT get a <name/>
        and <company_name/> from 'resellerlist', but an <alias/> and a
        <company/>.
        """
        handle = xml_reseller.get_str_value('handle')
        ret = cls(core, handle)
        ret._update_from_xml(xml_reseller)
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

    def _update_from_xml(self, xml_reseller):
        # FIXME: more fields..
        self._alias = xml_reseller.get_str_value('alias')
        self._company_name = xml_reseller.get_str_value('company')

    def _update(self):
        raise NotImplementedError()

    def __repr__(self):
        return f'<OxxapyReseller({self._handle})>'

    @property
    def handle(self):
        return self._handle


class OxxapyResellerNone(OxxapyReseller):
    """
    A special (immutable) NONE reseller

    We use this instead of None because the None argument signifies "unset",
    whereas we want to have No-Reseller as an option.
    """
    def __init__(self):
        # NOTE: We set handle to the empty string, because that is what we use
        # when calling domain_upd when unsetting the identity-reseller.
        # NOTE: However, it appears that it is impossible to unset a Reseller
        # at this time.
        super().__init__(core=None, handle='')

    def __repr__(self):
        return f'<OxxapyReseller[NONE]>'


OxxapyReseller.NONE = OxxapyResellerNone()


class OxxapyResellers(Manager):
    "Unbound reseller manager"
    def __init__(self, core):
        self._core = core

    def get(self, handle):
        "Get a single bound reseller"
        return self._core._cache_get(
            OxxapyReseller, handle, (lambda: (
                OxxapyReseller(self._core, handle))))

    def all(self):
        "Get all resellers"
        return self.filter()

    def filter(self, handle=None, name=None, company_name=None, alias=None):
        "Get all resellers that fit the filter expression"
        params = {'records': -1}

        assert handle is None, NotImplemented
        assert name is None, NotImplemented
        assert company_name is None, NotImplemented
        assert alias is None, NotImplemented

        # > Variabelen:
        # > - HANDLE (optioneel) Zoekwaarde voor de identity handle.
        # > - NAME (optioneel) Zoekwaarde voor de naam.
        # > - COMPANY_NAME (optioneel) Zoekwaarde voor bedrijfsnaam.
        # > - ALIAS (optioneel) Zoekwaarde voor de alias.
        # > - SORTNAME (optioneel) Veld waarop gesorteerd moet worden.
        # > - SORTORDER (optioneel) Sorteervolgorde (ASC of DESC).
        # > - START (optioneel) Bij welk veld moet worden begonnen met weergave
        # >   (standaard: 0).
        # > - RECORDS (optioneel) Hoeveel records moeten er worden weergegeven
        # >   (standaard: 25, -1 is alles)
        resp = self._core._call('resellerlist', **params)
        details = resp.get_child('details')
        ret = []

        self._core._cache_clear(OxxapyReseller)
        for xml_reseller in details.get_children('identity'):
            reseller = OxxapyReseller.from_xml(self._core, xml_reseller)
            self._core._cache_set(OxxapyReseller, reseller.handle, reseller)
            ret.append(reseller)

        ret.sort()
        return ret

    def none(self):
        "Return the NONE reseller, useful when filtering/unsetting"
        return OxxapyReseller.NONE
