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

"""
from .core import OxxapyCore
from .domain import OxxapyDomains


class Oxxapy(OxxapyCore):
    """
    OXXA API interface

    Prefer using the managers (like .domains) that provide a higher
    level interface.

    Example:

        api = Oxxapy(...)

        for domain in api.domains.all():
            print(domain)

    You can fall to direct API calls using the raw() method, if a higher
    level interface is missing. See the API docs (pdf) for more details.
    But remember that the return value (OxxapyOrder) might not not be
    very stable yet.
    """
    domains = OxxapyDomains.as_property()

    def raw(self, command, **params):
        """
        Do a raw API call directly

        Example:

            api.raw('domain_inf', sld='example', tld='com')

        Return value is an OxxapyOrder instance.
        """
        return self._call(command, **params)
