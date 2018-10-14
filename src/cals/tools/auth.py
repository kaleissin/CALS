from __future__ import unicode_literals


def may_edit_lang(user, language):
    """May <user> edit <language>?

    Returns tuple-in-tuple so that the inner tuple can be discarded easier:
    may_edit, _ = may_edit_lang(user, lang)

    Returns (may_edit, (is_admin, is_manager))
    """
    standard_return = True, (False, False)
    error_return = False, (False, False)

    # Must have a profile
    try:
        profile = user.profile
    except AttributeError:
        return error_return

    if user.is_superuser:
        return True, (True, True)
    if user == language.manager:
        return True, (False, True)
    if user in language.editors.all():
        return standard_return
    if language.public:
        return standard_return
    return error_return
