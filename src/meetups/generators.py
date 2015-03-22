from __future__ import unicode_literals

import random
import string
from itertools import permutations

from verification.generators import AbstractAlphabetKeyGenerator

__all__ = ['CALSGenerator']


class CALSGenerator(AbstractAlphabetKeyGenerator):
    alphabet = string.lowercase + string.digits
    length = 5
    name = 'cals'

    def generate_one_key(self, *args):
        keyset = set()
        key = super(CALSGenerator, self).generate_one_key(*args)
        while len(keyset) != self.length:
            key = super(CALSGenerator, self).generate_one_key(*args)
            keyset = set(key)
        return key

    def valid_key(self, key):
        keyset = set(key)
        return self.valid_re.search(key) and len(keyset) == len(key)

    def generate_all_keys(self, *args):
        rawkeylist = permutations(self.alphabet, self.length)
        return (''.join(rawkey) for rawkey in rawkeylist)

    def generate_n_keys(self, numkeys=0, *args):
        allkeys = tuple(self.generate_all_keys(*args))
        if not numkeys:
            return allkeys
        return random.sample(allkeys, numkeys)
