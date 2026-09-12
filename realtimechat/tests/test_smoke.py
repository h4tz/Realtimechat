"""Smoke test to verify test infrastructure works."""
import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_user_creation(user):
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.check_password("testpass123")


@pytest.mark.django_db
def test_two_users(other_user):
    assert User.objects.count() == 1
    assert other_user.username == "otheruser"
