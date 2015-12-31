from __future__ import unicode_literals
from __future__ import absolute_import

import random
import string
from itertools import permutations
import time
from datetime import date

from verification.generators import AbstractAlphabetKeyGenerator
from six.moves import range

__all__ = ['CALSGenerator']


class CALSGenerator(AbstractAlphabetKeyGenerator):
    alphabet = string.ascii_lowercase + string.digits
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

class ZeroPaddedNumberGenerator(AbstractAlphabetKeyGenerator):
    """From 0 to <max>, zero-padded to <length>"""
    pad_template = '%%0%is'
    length = 4

    def __init__(self, pad_template=None, *args, **kwargs):
        super(ZeroPaddedNumberGenerator, self).__init__(*args, **kwargs)
        self.pad_template = pad_template or self.pad_template
        self.maximum = maximum or self.maximum
        self._maximum = self.maximum + 1
        self.padder = self.pad_template % self.length

    def _pad(self, sample):
        return self.padder % sample

    def generate_one_key(self, *args):
        sample = random.randint(0, self._maximum)
        return self._pad(sample)

    def generate_all_keys(self, *args):
        samples = range(0, self._maximum)
        for i, sample in enumerate(samples):
            samples[i] = self._pad(sample)
        return samples

    def generate_n_keys(self, numkeys=0, *args):
        samples = random.sample(range(0, self._maximum), numkeys)
        if not numkeys:
            return self.generate_all_keys(*args)
        for i, sample in enumerate(samples):
            samples[i] = self._pad(sample)
        return samples

class HexColorGenerator(ZeroPaddedNumberGenerator):
    alphabet = string.digits + 'abcdef'
    length = 6
    maximum = 0xffffff
    pad_template = '#%%0%is'
    name = 'hexcolor'

    def __init__(self, pad_template=None, *args, **kwargs):
        super(HexColorGenerator, self).__init__(*args, **kwargs)
        self.valid_re = re.compile(r'^#[0-9a-f]{%i}$' % self.length)

class IsoDateGenerator(AbstractAlphabetKeyGenerator):
    alphabet = string.digits
    length = 8
    date_max = date.max
    date_min = date.min
    name = 'isodate'

    def __init__(self, date_min=None, date_max=None, *args, **kwargs):
        super(IsoDateGenerator, self).__init__(*args, **kwargs)
        self.date_max = date_max if date_max else self.date_max
        self.date_min = date_min if date_min else self.date_min

    def _date_range(self):
        return (
            int(time.mktime(self.date_min.timetuple())),
            int(time.mktime(self.date_max.timetuple()))
        )

    def _format(self, date):
        return date.strftime('%Y-%m-%d')

    def generate_one_key(self, *args):
        sample = random.randint(self._date_range())
        return self.format(date.fromtimestamp(sample))

    def generate_n_keys(numkeys=0, *args):
        samples = random.sample(range(self._date_range()), numkeys)
        for i, sample in enumerate(samples):
            samples[i] = self.format(date.fromtimestamp(sample))
        return samples
