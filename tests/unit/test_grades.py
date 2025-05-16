# tests/unit/test_grades.py
import pytest
from app.models import Unit, Task

@pytest.mark.usefixtures("client")
def test_weighted_grade_calculation(client):
    # 1) SIGN UP & ADD UNIT (include target_score)
    client.post(
        "/signup",
        data={"email": "bob@x.com", "password": "Abc123$%"},
        follow_redirects=True
    )
    client.post(
        "/api/add_unit",
        data={
            "name":         "CITS3403",
            "unit_code":    "CITS3403",
            "semester":     "1",
            "year":         "2025",
            "target_score": "80"
        },
        follow_redirects=True
    )

    # 2) fetch the unit
    with client.application.app_context():
        unit = Unit.query.first()
        assert unit is not None

    # 3) add two 50%-weighted tasks
    client.post(
        "/api/add_task",
        data={
            "unit_id":   unit.id,
            "task_name": "T1",
            "score":     "80",
            "weight":    "50",
            "date":      "2025-05-01",
            "type":      "assignment"
        },
        follow_redirects=True
    )
    client.post(
        "/api/add_task",
        data={
            "unit_id":   unit.id,
            "task_name": "T2",
            "score":     "100",
            "weight":    "50",
            "date":      "2025-06-01",
            "type":      "exam"
        },
        follow_redirects=True
    )

    # 4) hit the dashboard and assert the computed average (90.0)
    rv = client.get("/dashboard")
    assert b"90.0" in rv.data
