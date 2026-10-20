import json
from unittest import mock
from urllib.parse import parse_qs, urlparse

from allauth.socialaccount.models import SocialAccount
from django.contrib.auth import authenticate, get_user_model
from django.contrib.messages import get_messages
from django.core.checks import run_checks
from django.test import TestCase, override_settings

from surecom_ui.auth.adapters import TenantSocialAccountAdapter, is_allowed_email
from surecom_ui.auth.backends import SuperuserPasswordBackend
from surecom_ui.auth.settings import MISSING_TENANT, entra_settings, parse_domains

User = get_user_model()

LOGIN_URL = "/accounts/microsoft/login/"
CALLBACK_URL = "/accounts/microsoft/login/callback/"


class FakeResponse:
    """Just enough of requests.Response for allauth's OAuth2 client and the Graph call"""

    def __init__(self, data, status_code=200):
        self.status_code = status_code
        self.text = json.dumps(data)
        self.content = self.text.encode()
        self.headers = {"content-type": "application/json"}
        self._data = data

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def graph_profile(email, **overrides):
    profile = {
        "id": f"id-{email}",
        "mail": email,
        "userPrincipalName": email,
        "givenName": "Aoife",
        "surname": "Byrne",
        "displayName": "Aoife Byrne",
        "mailNickname": email.split("@")[0],
    }
    profile.update(overrides)
    return profile


class MicrosoftSignInMixin:
    """Runs the real allauth flow, with Microsoft's token and Graph endpoints mocked"""

    def sign_in(self, profile, next_url=None):
        start = self.client.post(LOGIN_URL + (f"?next={next_url}" if next_url else ""))
        self.assertEqual(start.status_code, 302)
        self.authorize_url = start["Location"]
        state = parse_qs(urlparse(self.authorize_url).query)["state"][0]

        session = mock.MagicMock()
        session.__enter__.return_value = session  # newer allauth uses `with session:`
        session.request.return_value = FakeResponse({"access_token": "token", "token_type": "Bearer"})
        session.get.return_value = FakeResponse(profile)
        with mock.patch.object(TenantSocialAccountAdapter, "get_requests_session", return_value=session):
            return self.client.get(CALLBACK_URL, {"code": "code", "state": state})

    def signed_in_user(self):
        return self.client.get("/").wsgi_request.user


class SettingsHelperTests(TestCase):
    def test_parse_domains(self):
        self.assertEqual(parse_domains(" Surecom.ie, @Example.com ,,"), ["surecom.ie", "example.com"])
        self.assertEqual(parse_domains(None), [])

    def test_missing_tenant_never_falls_back_to_common(self):
        app = entra_settings(environ={})["SOCIALACCOUNT_PROVIDERS"]["microsoft"]["APPS"][0]
        self.assertEqual(app["settings"]["tenant"], MISSING_TENANT)

    def test_https_callbacks_only_outside_debug(self):
        self.assertEqual(entra_settings(debug=False, environ={})["ACCOUNT_DEFAULT_HTTP_PROTOCOL"], "https")
        self.assertNotIn("ACCOUNT_DEFAULT_HTTP_PROTOCOL", entra_settings(debug=True, environ={}))

    def test_email_allowlist(self):
        self.assertTrue(is_allowed_email("Aoife@SURECOM.ie"))
        self.assertFalse(is_allowed_email("aoife@gmail.com"))
        self.assertFalse(is_allowed_email("aoife_gmail.com#EXT#@surecomltd.onmicrosoft.com"))
        self.assertFalse(is_allowed_email(""))
        with override_settings(SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS=[]):
            self.assertFalse(is_allowed_email("aoife@surecom.ie"))


class SuperuserPasswordBackendTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("root", "root@surecom.ie", "pw")
        self.staff = User.objects.create_user("staff", "staff@surecom.ie", "pw", is_staff=True)

    def test_only_superusers_authenticate_with_a_password(self):
        self.assertEqual(authenticate(username="root", password="pw"), self.superuser)
        self.assertIsNone(authenticate(username="staff", password="pw"))
        self.assertIsNone(authenticate(username="root", password="wrong"))

    def test_get_user_works_for_everyone(self):
        # Runs on every request; restricting it would sign out non-superusers
        self.assertEqual(SuperuserPasswordBackend().get_user(self.staff.pk), self.staff)


class MicrosoftSignInTests(MicrosoftSignInMixin, TestCase):
    def test_authorize_url_uses_company_tenant(self):
        self.sign_in(graph_profile("aoife@surecom.ie"))

        self.assertTrue(self.authorize_url.startswith(
            "https://login.microsoftonline.com/tenant-123/oauth2/v2.0/authorize"
        ))

    def test_first_sign_in_creates_user(self):
        response = self.sign_in(graph_profile("aoife@surecom.ie"))

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        user = User.objects.get(email="aoife@surecom.ie")
        self.assertEqual((user.first_name, user.last_name), ("Aoife", "Byrne"))
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_staff)
        self.assertEqual(self.signed_in_user(), user)

    def test_next_url_is_kept(self):
        response = self.sign_in(graph_profile("aoife@surecom.ie"), next_url="/somewhere/")

        self.assertRedirects(response, "/somewhere/", fetch_redirect_response=False)

    def test_returning_user_reuses_account(self):
        self.sign_in(graph_profile("aoife@surecom.ie"))
        self.client.logout()
        self.sign_in(graph_profile("aoife@surecom.ie"))

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialAccount.objects.count(), 1)
        self.assertEqual(self.signed_in_user().email, "aoife@surecom.ie")

    def test_existing_user_is_linked_and_keeps_password(self):
        existing = User.objects.create_superuser("aoife", "Aoife@Surecom.ie", "break-glass")

        self.sign_in(graph_profile("aoife@surecom.ie"))

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialAccount.objects.get().user, existing)
        self.assertEqual(self.signed_in_user(), existing)
        existing.refresh_from_db()
        self.assertTrue(existing.check_password("break-glass"))

    def test_other_domain_is_rejected(self):
        response = self.sign_in(graph_profile("someone@gmail.com"))

        self.assertRedirects(response, "/accounts/login/", fetch_redirect_response=False)
        self.assertFalse(User.objects.exists())
        self.assertFalse(self.signed_in_user().is_authenticated)
        self.assertIn("company Microsoft 365", str(list(get_messages(response.wsgi_request))[0]))

    def test_guest_account_is_rejected(self):
        guest = graph_profile(
            "partner@contractor.com",
            userPrincipalName="partner_contractor.com#EXT#@surecomltd.onmicrosoft.com",
        )
        self.sign_in(guest)

        self.assertFalse(User.objects.exists())

    def test_returning_user_rejected_if_address_no_longer_allowed(self):
        self.sign_in(graph_profile("aoife@surecom.ie"))
        self.client.logout()

        with override_settings(SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS=["other.ie"]):
            self.sign_in(graph_profile("aoife@surecom.ie"))
            self.assertFalse(self.signed_in_user().is_authenticated)

    def test_inactive_user_cannot_sign_in(self):
        User.objects.create_user("aoife", "aoife@surecom.ie", is_active=False)

        response = self.sign_in(graph_profile("aoife@surecom.ie"))

        self.assertFalse(self.signed_in_user().is_authenticated)
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get(response["Location"]), "Account disabled")


class SignInPagesTests(TestCase):
    def test_login_page_offers_microsoft_only(self):
        response = self.client.get("/accounts/login/?next=/somewhere/")

        self.assertContains(response, "Sign in with Microsoft")
        self.assertContains(response, 'action="/accounts/microsoft/login/?process=login&amp;next=%2Fsomewhere%2F"')
        self.assertNotContains(response, 'type="password"')

    def test_password_login_is_refused(self):
        User.objects.create_superuser("root", "root@surecom.ie", "pw")

        self.client.post("/accounts/login/", {"login": "root@surecom.ie", "password": "pw"})

        self.assertFalse(self.client.get("/").wsgi_request.user.is_authenticated)

    def test_signup_and_password_reset_are_gone(self):
        self.assertEqual(self.client.get("/accounts/signup/").status_code, 404)
        self.assertEqual(self.client.get("/accounts/password/reset/").status_code, 404)

    def test_base_template_signs_out_through_allauth(self):
        user = User.objects.create_user("aoife", "aoife@surecom.ie")
        self.client.force_login(user)

        response = self.client.get("/accounts/logout/")

        self.assertEqual(response.context["surecom_ui"]["logout_url"], "/accounts/logout/")
        self.client.post("/accounts/logout/")
        self.assertFalse(self.client.get("/").wsgi_request.user.is_authenticated)


class AdminAccessTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser("root", "root@surecom.ie", "pw")
        self.staff = User.objects.create_user("staff", "staff@surecom.ie", "pw", is_staff=True)
        self.user = User.objects.create_user("user", "user@surecom.ie", "pw")

    def test_signed_out_admin_goes_to_microsoft_sign_in(self):
        response = self.client.get("/admin/", follow=True)

        self.assertEqual(response.redirect_chain[-1][0], "/accounts/login/?next=%2Fadmin%2F")

    def test_non_staff_get_403(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get("/admin/login/").status_code, 403)

    def test_staff_signed_in_with_microsoft_reach_admin(self):
        self.client.force_login(self.staff)

        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_break_glass_accepts_superuser_password(self):
        response = self.client.post("/admin/break-glass/", {"username": "root", "password": "pw", "next": "/admin/"})

        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/admin/").wsgi_request.user, self.superuser)

    def test_break_glass_rejects_staff_password(self):
        response = self.client.post("/admin/break-glass/", {"username": "staff", "password": "pw"})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class SystemCheckTests(TestCase):
    def ids(self):
        return {issue.id for issue in run_checks()}

    def test_configured_settings_pass(self):
        self.assertFalse({i for i in self.ids() if i.startswith("surecom_auth")})

    def test_missing_configuration_warns(self):
        with override_settings(**{k: v for k, v in entra_settings(environ={}).items()
                                  if k in ("SOCIALACCOUNT_PROVIDERS", "SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS")}):
            self.assertTrue({"surecom_auth.W001", "surecom_auth.W002"} <= self.ids())

    def test_app_order_warns(self):
        from django.conf import settings

        apps = [a for a in settings.INSTALLED_APPS if a != "surecom_ui.auth"] + ["surecom_ui.auth"]
        with override_settings(INSTALLED_APPS=apps):
            self.assertIn("surecom_auth.W004", self.ids())
