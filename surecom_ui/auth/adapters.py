import logging

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def allowed_email_domains():
    """Lower-cased domains from SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS"""
    return [d.lower() for d in getattr(settings, "SURECOM_AUTH_ALLOWED_EMAIL_DOMAINS", [])]


def is_allowed_email(email):
    """True if the email's domain is in the allowlist. An empty allowlist allows no one."""
    if not email or "@" not in email:
        return False
    return email.rsplit("@", 1)[1].lower() in allowed_email_domains()


def microsoft_email(sociallogin):
    """
    The address Microsoft asserted for this sign-in.

    Read from the Graph profile rather than ``sociallogin.user``, which is the
    local user for returning sign-ins. Guests have an external ``mail`` and an
    ``#EXT#`` UPN, so neither passes the domain check.
    """
    extra = sociallogin.account.extra_data or {}
    return (extra.get("mail") or extra.get("userPrincipalName") or sociallogin.user.email or "").strip()


class TenantSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Restricts Microsoft sign-in to company addresses and links existing users.

    allauth's own email linking doesn't apply: the Microsoft provider doesn't
    mark emails as verified, and allauth's email authentication also wipes the
    matched user's password, which would disable a break-glass superuser who
    shares their M365 address. So the link is made here instead.
    """

    def pre_social_login(self, request, sociallogin):
        email = microsoft_email(sociallogin)

        if not is_allowed_email(email):
            logger.warning("Microsoft sign-in rejected for %r: domain not allowed", email)
            messages.error(
                request,
                f"{email or 'That account'} can't sign in here. "
                "Use your company Microsoft 365 account.",
            )
            raise ImmediateHttpResponse(redirect("account_login"))

        if sociallogin.is_existing:
            return

        user = get_user_model().objects.filter(email__iexact=email).first()
        if user is not None:
            logger.info("Linking Microsoft sign-in for %s to existing user %s", email, user.pk)
            sociallogin.connect(request, user)
