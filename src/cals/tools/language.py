from __future__ import unicode_literals, absolute_import

import random

from cals.language.models import Language


def random_conlang():
    conlangs = (Language.objects
        .conlangs()
        .filter(features__isnull=False)
        .distinct()
        .values_list('slug', flat=True)
    )
    return random.choice(conlangs)


def conlangs_with_homes():
    conlangs = Language.objects.conlangs().exclude(homepage='')
    return conlangs
