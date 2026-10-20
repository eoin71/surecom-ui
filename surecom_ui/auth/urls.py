from allauth.account.decorators import secure_admin_login
from django.contrib import admin
from django.urls import include, path


def entra_urlpatterns(admin_site=None, break_glass_path="admin/break-glass/"):
    """
    URL patterns for Microsoft sign-in. List them BEFORE ``path("admin/", ...)``:

        urlpatterns = [
            *entra_urlpatterns(admin.site),
            path("admin/", admin.site.urls),
            ...
        ]

    - ``admin/login/`` sends signed-out visitors to Microsoft sign-in, and
      signed-in non-staff get a 403. It shadows the admin's own login URL, so
      the admin's redirects (``reverse("admin:login")``) land here.
    - ``admin/break-glass/`` is the admin's stock password form. Only a
      superuser can pass it, because of SuperuserPasswordBackend. It must come
      before ``admin/``, or the admin's catch-all view swallows it.
    - ``accounts/`` is allauth (sign-in, sign-out, Microsoft callback).
    """
    site = admin_site or admin.site
    return [
        path("admin/login/", secure_admin_login(site.login)),
        path(break_glass_path, site.login, name="surecom_break_glass"),
        path("accounts/", include("allauth.urls")),
    ]
