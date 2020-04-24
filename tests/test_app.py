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


@pytest.mark.parametrize('count_messages', ('100', '-10', 'abc'))
def test_get_last_messages_bad_request(test_client: TestClient, count_messages):
    response = test_client.get(f'/messages/last/{count_messages}')
    assert response.status_code == 404
    if count_messages == 'abc':
        assert 'Count of last messages must be a number' in response.text
    else:
        assert 'Count of last messages must be less that 50 and more 0' in response.text


def test_last_messages(test_client: TestClient):
    with test_client.websocket_connect('/ws/name') as ws:
        ws.send_text('message')
    response = test_client.get('/messages/last/50')
    assert response.status_code == 200
    assert 'name' in response.text and 'message' in response.text


def test_ws_endpoint(test_client: TestClient):
    with test_client.websocket_connect('/ws/name') as ws:
        ws.send_text('message')
        message = ws.receive_text()
        assert message == 'name: message'


def test_chat_logic(test_client: TestClient):
    with test_client.websocket_connect(
        '/ws/name1'
    ) as ws1, test_client.websocket_connect('/ws/name2') as ws2:
        ws1.send_text('name1 send message to name2')
        message = ws2.receive_text()
        assert message == 'name1: name1 send message to name2'
