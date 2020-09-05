"""Mixin Objects that allow for shared methods"""


class GetHeaders(object):
    """Mixin to get a header"""
    def get_header_value(self, name):
        """
        Returns the header value of the header defined in ``name``

        :param name: ``str`` name of the header to get the value of
        """
        for x in self.raw_entry["headers"]:
            if x["name"].lower() == name.lower():
                return x["value"]


class MimicDict(object):
    """Mixin for functions to mimic a dictionary for backward compatibility"""

    def __getitem__(self, item):
        return self.raw_entry[item]

    def __len__(self):
        return len(self.raw_entry)

    def get(self, item, default=None):
        """
            Mimics dict.get()
        """
        return self.raw_entry.get(item, default)

    def keys(self):
        """
            Mimics dict.keys()
        """
        return self.raw_entry.keys()

    def items(self):
        """
            Mimics dict.items()
        """
        return self.raw_entry.items()