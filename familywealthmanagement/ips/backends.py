from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import Investor
from .utils import normalize_phone


class IdentifierBackend(ModelBackend):
    """Log in with a username, or with the email or phone number on the investor profile."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        user = super().authenticate(request, username=username, password=password, **kwargs)
        if user is not None or not username or password is None:
            return user
        query = Q(email__iexact=username.strip())
        phone = normalize_phone(username)
        if phone:
            query |= Q(phone=phone)
        investor = Investor.objects.filter(query).select_related('user').first()
        if investor is None or investor.user is None:
            return None
        # Reuse the standard check (password, is_active) with the resolved username.
        return super().authenticate(request, username=investor.user.get_username(), password=password)
