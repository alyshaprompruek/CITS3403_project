def test_signup_and_login(client):
    # sign up
    rv = client.post("/signup", data={
        "email":    "alice@example.com",
        "password": "Secret123!"
    }, follow_redirects=True)
    assert b"dashboard" in rv.data

    # logout
    client.post("/api/logout")

    # login success
    rv = client.post("/login", data={
        "email":    "alice@example.com",
        "password": "Secret123!"
    }, follow_redirects=True)
    assert b"dashboard" in rv.data

    # login failure
    rv = client.post("/login", data={
        "email":    "alice@example.com",
        "password": "WrongPass"
    }, follow_redirects=True)
    assert b"Invalid email or password" in rv.data
