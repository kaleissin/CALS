from __future__ import unicode_literals

import random
import string

from verification.generators import AbstractAlphabetKeyGenerator

__all__ = ['CALSGenerator']


class CALSGenerator(AbstractAlphabetKeyGenerator):
    alphabet = string.lowercase + string.digits
    length = 5

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
        bucketsize = self.alphabet // self.length
        bigset = set()
        for a in self.alphabet[:bucketsize]:
            for b in self.alphabet[bucketsize:bucketsize*2]:
                for c in self.alphabet[bucketsize*2:bucketsize*3]:
                    for d in self.alphabet[bucketsize*3:bucketsize*4]:
                        for e in self.alphabet[bucketsize*4:]:
                            bigset.add((a,b,c,d,e))
        biglist = []
        for ntuple in bigset:
            ntuple = list(ntuple)
            random.shuffle(ntuple)
            biglist = ''.join(ntuple)
        return biglist

    def generate_n_keys(self, numkeys=0, *args):
        allkeys = self.generate_all_keys(*args)
        if not numkeys:
            return allkeys
        return random.sample(allkeys, numkeys)
