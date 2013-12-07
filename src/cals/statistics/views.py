import logging
_LOG = logging.getLogger(__name__)
_LOG.info(__name__)

from django.shortcuts import render

from cals.statistics import generate_global_stats
from cals.statistics import generate_feature_stats
from cals.statistics import generate_people_stats
from cals.statistics import generate_vocabulary_stats
from cals.statistics import generate_langname_stats
from cals.statistics import generate_averageness_stats
from cals.statistics import generate_milestone_stats

def show_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data.update(generate_global_stats())
    return render(request, 'statistics/index.html', data)

def show_feature_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data['features'] = generate_feature_stats()
    return render(request, 'statistics/features.html', data)

def show_people_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data['users'] = generate_people_stats()
    return render(request, 'statistics/people.html', data)

def show_vocab_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data['vocabulary'] = generate_vocabulary_stats()
    return render(request, 'statistics/vocabulary.html', data)

def show_langname_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data['name'] = generate_langname_stats()
    return render(request, 'statistics/langnames.html', data)

def show_averageness_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data['averageness'] = generate_averageness_stats()
    return render(request, 'statistics/averageness.html', data)

def show_milestone_stats(request, *args, **kwargs):
    me = 'statistics'
    data = {'me': me}

    data['milestones'] = generate_milestone_stats()
    return render(request, 'statistics/milestones.html', data)

