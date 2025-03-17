import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_get_user_gists(client):
    response = client.get('/octocat')
    assert response.status_code == 200
    assert 'gists' in response.json
    assert 'page' in response.json
    assert response.json['page'] == 1
    assert response.json['per_page'] == 5

def test_pagination(client):
    response = client.get('/octocat?page=2&per_page=3')
    assert response.status_code == 200
    assert response.json['page'] == 2
    assert response.json['per_page'] == 3

def test_clear_all_cache(client):
    # First make a request to cache some data 
    client.get('/octocat')
    
    # Clear all cache
    response = client.post('/cache/clear')
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert 'Entire cache cleared' in response.json['message']

def test_clear_user_specific_cache(client):
    # First make a request to cache some data
    client.get('/octocat')
    
    # Clear cache for specific user
    response = client.post('/cache/clear?username=octocat')
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert 'Cache cleared for user: octocat' in response.json['message']