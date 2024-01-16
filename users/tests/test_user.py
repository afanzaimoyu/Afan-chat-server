import pytest
from asgiref.testing import ApplicationCommunicator
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from users.user_tools.tools import get_token
from users.consumers import ChatConsumer

@pytest.fixture
def user():
    return get_user_model().objects.create_user(username='test', password='test')

@pytest.fixture
def sample_html_content():
    return """
    <html>
        <head>
            <title>Sample Title</title>
            <meta name="description" content="Sample Description">
            <meta name="keywords" content="Keyword1, Keyword2">
            <link type="image/x-icon" href="/favicon.ico">
        </head>
        <body>
            <h1>Sample Body</h1>
        </body>
    </html>
    """

@pytest.mark.django_db
def test_prioritized_url_discover(sample_html_content):
    discover = PrioritizedUrlDiscover()

    with patch('requests.get') as mock_get:
        mock_get.return_value.text = sample_html_content

        content_map = discover.get_url_content_map(sample_html_content)

        assert content_map

        url_content = content_map["http://www.example.com"]
        assert url_content["title"] == "Sample Title"
        assert url_content["description"] == "Sample Description"
        assert url_content["image"] == "/favicon.ico"
