# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""


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
