import enum
from typing import Dict, Optional, Type

from . import api


class Strings():

    @staticmethod
    def build_enums():
        """ Builds the enums for the API. """
        ret: Dict[str, Type[enum.IntEnum]] = {}
        for key, value in api.get_string().items():
            enum_name = key
            # 65, 66; 137, 138 have the same string description
            enum_values = [
                (_['string'], _['id'])
                for _ in value
                if _['id'] not in {66, 138}
            ]
            enum_class = enum.IntEnum(enum_name, enum_values)
            ret[key] = enum_class
        return ret

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Strings, cls).__new__(cls)
        cls._content = None
        return cls._instance

    @property
    def content(self):
        if self._content is None:
            self._content = self.build_enums()
        return self._content

    def __getitem__(self, key: str):
        return self.content[key]

    def query(self, category: str, key: str) -> Optional[int]:
        """ Queries the string API for a string. """
        if category not in self.content or key is None:
            return None
        return self.content[category][key].value

    def query_id(self, category: str, key: int) -> Optional[str]:
        """ Queries the string API for an ID. """
        if category not in self.content or key is None:
            return None
        return self.content[category](key).name
