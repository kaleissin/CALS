from django.core.management.base import BaseCommand

from cals.tools.dump import dump


DIR_DEFAULT = '/tmp/calscsv'


class Command(BaseCommand):
    help = "Dump a CSV version of specific models to file"

    def add_arguments(self, parser):
        parser.add_argument(
            '--directory',
            type=str,
            default=DIR_DEFAULT,
            help='Directory to store CSV in',
        ) 

    def handle(self, *args, **options):
        path = options['directory']
        dump(path)
