from django.contrib.auth.backends import ModelBackend


class SuperuserPasswordBackend(ModelBackend):
    """
    Password sign-in for active superusers only (the break-glass account).

    Everyone else signs in with Microsoft. allauth logs those users in with the
    first configured backend that has ``get_user``, so this can be the only
    backend: sessions and permissions work for every user, but no one except a
    superuser can authenticate with a password.

    ``get_user`` and ``user_can_authenticate`` are deliberately not changed:
    ``get_user`` runs on every request, and restricting it would sign out
    everyone who isn't a superuser.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None and user.is_superuser:
            return user
        return None
