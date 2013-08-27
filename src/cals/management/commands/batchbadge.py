from datetime import datetime, timedelta
import sys
sys.path.append('/home/python/django-trunk/')
sys.path.append('/home/python/django-sites/')
sys.path.append('/home/python/django-sites/CALS/')

from django.db.models import Q, F
from django.core.management import setup_environ
from django.core.management.base import NoArgsCommand, BaseCommand

import settings
setup_environ(settings)

from cals.models import *
from translations.models import *
from relay.models import *
from phonemes.models import Sound
from nano.badge.models import Badge
from nano.tools import get_user_model, get_profile_model
from nano.privmsg.models import PM
from nano.mark.models import *
from nano.comments.models import Comment

from cals.people.models import user_unlurked

Profile = get_profile_model()
User = get_user_model()

def batchbadge(badge, models):
    for model in models:
        if badge not in model.badges.all():
            model.badges.add(badge)

def unlurk():
    brs = Badge.objects.get_all_recipients().filter(profile__is_lurker=True)
    unlurked = Profile.objects.filter(user__in=brs)
    exlurker_count = unlurked.count()
    unlurked.update(is_lurker=False)
    # Right way: method on Profile.objects that sends this signal
    for ul in unlurked:
        user_unlurked.send(sender=ul, user=ul.user)
    return exlurker_count

def developers():
    # Cannot use signal
    badge = Badge.objects.get(name='Developer')
    developers = User.objects.filter(id__in=(1, 2))
    batchbadge(badge, developers)

def early_birds():
    # Pointless to use signal
    badge = Badge.objects.get(name='Early bird')
    early_birds = User.objects.filter(date_joined__lte='2008-06-07')
    batchbadge(badge, early_birds)

def conlangers():
    """Mark conlangers as just that.

    Redundant, done by signal in cals.models"""
    badge = Badge.objects.get(name='Conlanger')
    editors = User.objects.filter(edits__isnull=False)
    batchbadge(badge, editors)
    managers = User.objects.filter(manages__isnull=False)
    batchbadge(badge, managers)

def nudgers():
    badge = Badge.objects.get(name='Nudger')
    nudgers = [u for u in User.objects.all() if u.pms_sent.count()]
    batchbadge(badge, nudgers)

def connoiseurs():
    badge = Badge.objects.get(name='Connoisseur')
    connoiseurs = [u for u in User.objects.all() 
            if u.marks.filter(marktype__slug__startswith='fav').count()]
    batchbadge(badge, connoiseurs)

# -- by date

def _active_year_ago(years):
    assert int(years)
    now = datetime.now()
    # averaged year
    x_years_ago = now - timedelta(days=years*365, seconds=6*60*60)
    # averaged month
    a_month_ago = now - timedelta(days=30, seconds=10.56*60*60)
    # Keep forgetting this, in datetimes:
    # < is before, earlier than
    # > is after, later than
    return [u for u in User.objects.all() 
            if u.date_joined <= x_years_ago and u.last_login > a_month_ago]

# 1 year
def yearlings():
    badge = Badge.objects.get(name='Yearling')
    yearlings = _active_year_ago(1)
    batchbadge(badge, yearlings)

# 2 years
def old_hands():
    badge = Badge.objects.get(name='Old Hand')
    old_hands = _active_year_ago(2)
    batchbadge(badge, old_hands)

# 3 years
def regulars():
    badge = Badge.objects.get(name='Regular')
    old_hands = _active_year_ago(3)
    batchbadge(badge, old_hands)

def boomerangs():
    badge = Badge.objects.get(name='Boomerang')
    week = timedelta(days=7)
    boomerangs = User.objects.filter(last_login__gt=F('date_joined')+week,
            badges__isnull=False).distinct()
    batchbadge(badge, boomerangs)

# -- helpers

def testbunnies():
    # Cannot use signal
    badge = Badge.objects.get(name='Test Bunny')
    testbunny_ids = (2, 37)
    testbunnies = User.objects.filter(id__in=testbunny_ids)
    batchbadge(badge, testbunnies)

def bughunters():
    # Cannot use signal
    badge = Badge.objects.get(name='Bughunter')
    bughunter_ids = (
            2, 3, 30, 32, 195, 
            87, 52, 90, 82, 86, 
            280, 326, 350, 147, 416,
            463, 314, 493, 184, 253
    )
    bughunters = User.objects.filter(id__in=bughunter_ids)
    batchbadge(badge, bughunters)

def dreamers():
    # Cannot use signal
    badge = Badge.objects.get(name='Dreamer')
    dreamer_ids = (
            2, 3, 27, 30, 37,
            195, 123, 52, 90, 
            55, 93, 87, 425
    )
    dreamers = User.objects.filter(id__in=dreamer_ids)
    batchbadge(badge, dreamers)

def autobiographers():
    badge = Badge.objects.get(name='Autobiographer')
    autobiographer_profiles = Profile.objects.autobiographers()
    autobiographers = User.objects.filter(id__in=[p.user_id for p in autobiographer_profiles])
    batchbadge(badge, autobiographers)

# -- translating
def translators():
    """Mark translators as just that.

    Redundant, done by signal in translations.models"""
    badge = Badge.objects.get(name='Translator')
    translators = [trans.translator for trans in Translation.objects.exclude(exercise=1)]
    batchbadge(badge, translators)

def civ4fans():
    badge = Badge.objects.get(name='CIV IV-fan')
    num_civ_exercises = TranslationExercise.objects.filter(category=4).count()
    translators = [u for u in User.objects.filter(translations__exercise__category=4).distinct() 
            if u.translations.filter(exercise__category=4).count() == num_civ_exercises]
    batchbadge(badge, translators)

# -- relay
def torchbearers():
    badge = Badge.objects.get(name='Torchbearer')
    torchbearers = [torch.participant.cals_user for torch in Torch.objects.all()
            if torch.participant.cals_user] 
    batchbadge(badge, torchbearers)

def relay_masters():
    badge = Badge.objects.get(name='Relay master')
    relay_masters = [relay.relay_master.cals_user for relay in Relay.objects.all()
            if relay.relay_master.cals_user] 
    batchbadge(badge, relay_masters)

def ring_masters():
    badge = Badge.objects.get(name='Ring master')
    ring_masters = [ring.ring_master.cals_user for ring in Ring.objects.all()
            if ring.ring_master.cals_user] 
    batchbadge(badge, ring_masters)

# -- comments
def phoneticians():
    badge = Badge.objects.get(name='Phonetician')
    phoneticians = [comment.user for comment in Comment.objects.all()
            if comment.content_type.model_class() == Sound] 
    batchbadge(badge, phoneticians)

def critics():
    badge = Badge.objects.get(name='Critic')
    critics = [comment.user for comment in Comment.objects.all()]
    batchbadge(badge, critics)

# -- tech
def timetravellers():
    badge = Badge.objects.get(name='Timetraveller')
    timetravellers = [profile.user for profile in Profile.objects.all()
            if profile.seen_ipv6] 
    batchbadge(badge, timetravellers)

_batch_jobs = {
        'connoiseurs': connoiseurs,
        'developers': developers,
        'early_birds': early_birds, 
        'conlangers': conlangers, 
        'translators': translators, 
        'civ4fans': civ4fans, 
        'autobiographers': autobiographers,
        'torchbearers': torchbearers, 
        'relay_masters': relay_masters, 
        'ring_masters': ring_masters,
        'bughunters': bughunters,
        'testbunnies': testbunnies,
        'dreamers': dreamers,
        'nudgers': nudgers,
        'yearlings': yearlings,
        'old_hands': old_hands,
        'boomerangs': boomerangs,
        'timetravellers': timetravellers,
        'phoneticians': phoneticians,
        'regulars': regulars,
}

def run_batch(verbose=True):
    for batch_name, batch_job in _batch_jobs.items():
        if verbose: print batch_name,
        batch_job()
        if verbose: print 'done'
    unlurked = unlurk()
    if verbose:
        print '\n%i users have become active' % unlurked

class Command(BaseCommand):
    help = "Recalculate and set badges for users"


    def handle(self, *args, **options):
        verbosity = bool(int(options.get('verbosity', 1)))
        run_batch(verbosity)

if __name__ == '__main__':
    run_batch()
