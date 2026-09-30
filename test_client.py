from app import create_app

app = create_app()
with app.test_client() as c:
    r = c.get('/auth')
    print('GET /auth', r.status_code, r.data.decode()[:200])
    r = c.get('/auth/')
    print('GET /auth/', r.status_code, r.data.decode()[:200])