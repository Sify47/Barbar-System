import json
import pytest
from app import create_app
from app.extensions import db

app = create_app()
app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
with app.app_context():
    db.create_all()

client = app.test_client()

# Test default pagination with empty database
response = client.get('/booking/list')
assert response.status_code == 200
payload = json.loads(response.data)
assert payload.get("page") == 1
assert payload.get("per_page") == 10
assert isinstance(payload.get("data"), list)

# Test custom pagination params
response2 = client.get('/booking/list?page=2&per_page=5')
assert response2.status_code == 200
payload2 = json.loads(response2.data)
assert payload2.get("page") == 2
assert payload2.get("per_page") == 5
