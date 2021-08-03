# vim: set ts=8 sw=4 sts=4 et ai tw=79:
"""
OXXA API Library in Python (oxxapy), licensed under the LGPLv3+.

Copyright (C) 2021 Walter Doekes, OSSO B.V.

See README.rst for more info.
"""
from xml.etree import ElementTree

from .exceptions import OxxapyApplicationError


class _OxxapyXml:
    def __init__(self, root, req):
        self._root = root
        self.orig_req = req

    def get_bool_value(self, tagname):
        "Return bool contents of immediate child with name tagname"
        return self._unmarshal_bool(self.get_str_value(tagname))

    def get_date_value(self, tagname):
        "Return date contents of immediate child with name tagname"
        return NotImplemented

    def get_int_value(self, tagname):
        "Return int contents of immediate child with name tagname"
        return int(self.get_str_value(tagname))

    def get_str_value(self, tagname):
        "Return string contents of immediate child with name tagname"
        return self._root.findtext(tagname)

#    def get_child(self, tagname):
#        "Return new _OxxapyXml with this only child"
#        children = self._root.findall(tagname)
#        if len(children) != 1:
#            raise OxxapyApplicationError(
#                0, '{} {} children'.format(len(children), tagname),
#                req=self.orig_req, resp=self)
#        return children[0]

    def get_children(self, tagname, wrapper_cb=None):
        "Return a list of children passed through wrapper_cb"
        ret = []
        for child in self._root.findall(tagname):
            if wrapper_cb:
                child = wrapper_cb(child, req=self.orig_req)
            ret.append(child)
        return ret

    def __str__(self):
        # FIXME: There will be an ElementTree.indent() in python3.9
        from xml.dom import minidom
        binstr = ElementTree.tostring(self._root)
        return minidom.parseString(binstr).toprettyxml(indent='  ')

    def __repr__(self):
        return '<{} to="{}", """{}""">'.format(
            self.__class__.__name__, self.orig_req, self)

    @classmethod
    def _unmarshal_bool(cls, val):
        assert val in ('TRUE', 'FALSE', 'Y', 'N'), val
        return val in ('TRUE', 'Y')

    @classmethod
    def _unmarshal_bool_or_pending(cls, val):
        if val == 'PENDING':
            return None
        return cls._unmarshal_bool(val)


class OxxapyResponse(_OxxapyXml):
    @classmethod
    def from_binstr(cls, binstr, req):
        root = ElementTree.fromstring(binstr)
        return cls(root=root, req=req)

    def extract_order(self):
        """
        Return inner <order/> from outer <channel/> as OxxapyOrder
        """
        if self._root.tag == 'channel':
            children = self._root.getchildren()
            if len(children) == 1 and children[0].tag == 'order':
                return OxxapyOrder(children[0], req=self.orig_req)
        raise NotImplementedError()


class OxxapyOrder(_OxxapyXml):
    def __init__(self, root, req):
        self._root = root
        self.orig_req = req

        self.order_id = int(self._root.findtext('order_id'))
        self._status_code = self._root.findtext('status_code')
        self._status_description = self._root.findtext('status_description')
        self._order_complete = self._unmarshal_bool_or_pending(
            self._root.findtext('order_complete'))
        self.done = self._unmarshal_bool(self._root.findtext('done'))

    @property
    def status(self):
        """
        Get (success, status_int, status_message) tuple
        """
        if self._status_code.startswith('XMLOK'):
            return (
                True, int(self._status_code[5:].lstrip()),
                self._status_description)
        elif self._status_code.startswith('XMLERR'):
            return (
                False, int(self._status_code[6:].lstrip()),
                self._status_description)
        raise NotImplementedError(self._status_code)

    def is_order_complete(self, status):
        assert status in (False, True, None), status  # 'false, true, pending'
        return self._order_complete is status
