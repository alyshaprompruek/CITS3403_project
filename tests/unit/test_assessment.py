# tests/unit/test_assessment.py
from app.models import Unit, Task

def test_add_assessment_to_unit(client):
    # 1) SIGN UP (and follow the redirect so the cookie is stored)
    client.post(
        "/signup",
        data={"email":"task@test.com","password":"Task123!"},
        follow_redirects=True
    )

    # 2) ADD UNIT (and follow the redirect so the unit really exists in this session)
    client.post(
        "/api/add_unit",
        data={
            "name":       "CITS3403",
            "unit_code":  "CITS3403",
            "semester":   "1",
            "year":       "2025",
            "target_score": "90"
        },
        follow_redirects=True
    )

    # 3) fetch that unit from the DB
    with client.application.app_context():
        unit = Unit.query.first()
        assert unit is not None

    # 4) ADD TASK (again following the redirect to pick up flashes/page state)
    rv = client.post(
        "/api/add_task",
        data={
            "unit_id":    unit.id,
            "task_name":  "Midterm",
            "score":      "75",
            "weight":     "20",
            "date":       "2025-05-10",
            "type":       "assignment"
        },
        follow_redirects=True
    )

    # 5) assert flash/message & DB row
    assert b"Task added successfully" in rv.data
    with client.application.app_context():
        tasks = Task.query.filter_by(unit_id=unit.id).all()
        assert len(tasks) == 1
        assert tasks[0].task_name == "Midterm"
