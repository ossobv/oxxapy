# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""


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
