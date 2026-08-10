import pytest


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="secretaria", password="senha-forte-123", email="secretaria@escola.test"
    )


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client
