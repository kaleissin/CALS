from __future__ import absolute_import
from __future__ import unicode_literals
from django.http import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test

from cals.tools.auth import may_edit_lang
from cals.language.models import Language

__all__ = ['MayEditMixin']

# CBV decorators and mixins


class MayEditMixin(object):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        language = Language.objects.get(slug=kwargs.get('language', None))
        may_edit, (admin, manager) = may_edit_lang(request.user, language)
        if not may_edit:
            error_msg = 'You are not authorized to edit "%s"' % language
            return HttpResponseForbidden(error_msg)
        self.user_is_manager = manager
        self.user_is_admin = admin
        return super(MayEditMixin, self).dispatch(request, *args, **kwargs)


class SuperUserMixin(object):

    @method_decorator(user_passes_test(lambda u: u.is_superuser))
    def dispatch(self, request, *args, **kwargs):
        return super(SuperUserMixin, self).dispatch(request, *args, **kwargs)
