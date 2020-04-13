import pytest
from async_chat.app import app
from fastapi.testclient import TestClient


@pytest.fixture()
def test_client():
    yield TestClient(app)


def test_get(test_client: TestClient):
    response = test_client.get('/name')
    assert response.status_code == 200
    assert 'Chat' in response.text


def test_get_last_messages_empty(test_client: TestClient):
    response = test_client.get('/messages/last50')
    assert response.status_code == 200


def test_last_messages(test_client: TestClient):
    with test_client.websocket_connect('/ws/name') as ws:
        ws.send_text('message')
    response = test_client.get('/messages/last50')
    assert response.status_code == 200
    assert 'name' in response.text and 'message' in response.text


def test_ws_endpoint(test_client: TestClient):
    with test_client.websocket_connect('/ws/name') as ws:
        ws.send_text('message')
        message = ws.receive_text()
        assert message == 'name: message'
