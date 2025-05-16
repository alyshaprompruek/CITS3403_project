from app.models import Unit

def test_add_unit(client):
    client.post("/signup", data={"email":"u@x.com","password":"Test123!"})
    rv = client.post("/api/add_unit", data={
        "name":        "CITS3403",
        "unit_code":   "CITS3403",
        "semester":    "1",
        "year":        "2025",
        "target_score":"85"
    }, follow_redirects=True)
    assert b"Unit added successfully" in rv.data

    with client.application.app_context():
        units = Unit.query.all()
        assert len(units) == 1
        assert units[0].unit_code == "CITS3403"
