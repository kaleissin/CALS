import csv
from io import StringIO
from pathlib import Path

from cals.language.models import Language
from cals.feature.models import (
    Feature,
    FeatureValue
)
from cals.language.models import LanguageName
from cals.languagefeature.models import LanguageFeature
from translations.models import (
    Translation,
    TranslationExercise
)

__all__ = ['dump']

models = (
        Language,
        LanguageName,
        LanguageFeature,
        Feature,
        FeatureValue,
        Translation,
        TranslationExercise,
)


def listofdicts2csv(dict_qs, File=StringIO()):
    keys = dict_qs[0].keys()
    writer = csv.DictWriter(File, keys, quoting=csv.QUOTE_NONNUMERIC,
                            extrasaction='ignore')
    writer.writerow(dict(zip(keys, keys)))
    for d in dict_qs:
        writer.writerow(d)
    return File


def dump(path='/tmp/calscsv/'):
    root = Path(path)
    if not root.exists():
        root.mkdir()
    for model in models:
        path = root / '{}.csv'.format(model.__name__)
        print(path)
        with path.open('w') as F:
            text = listofdicts2csv(model.objects.values(), F)
            F.close()


if __name__ == '__main__':
    dump()
