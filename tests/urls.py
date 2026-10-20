from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import path

from surecom_ui.auth.urls import entra_urlpatterns


@login_required
def home(request):
    return HttpResponse(f"home:{request.user.email}")


urlpatterns = [
    *entra_urlpatterns(admin.site),
    path("admin/", admin.site.urls),
    path("", home, name="home"),
]
