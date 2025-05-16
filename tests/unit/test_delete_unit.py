# tests/unit/test_delete_unit.py
import pytest
from app.models import Unit, Task

@pytest.mark.usefixtures("client")
def test_delete_unit_and_tasks(client):
    # 1) SIGN UP & ADD UNIT (with target_score so it will pass validation)
    client.post(
        "/signup",
        data={"email": "del@x.com", "password": "Del123#"},
        follow_redirects=True
    )
    client.post(
        "/api/add_unit",
        data={
            "name":         "CITS3403",
            "unit_code":    "CITS3403",
            "semester":     "1",
            "year":         "2025",
            "target_score": "85"
        },
        follow_redirects=True
    )

    # 2) fetch the unit
    with client.application.app_context():
        unit = Unit.query.first()
        assert unit is not None

    # 3) ADD A TASK (so we can verify it's also deleted)
    client.post(
        "/api/add_task",
        data={
            "unit_id":   unit.id,
            "task_name": "Ex1",
            "score":     "50",
            "weight":    "100",
            "date":      "2025-05-01",
            "type":      "exam"
        },
        follow_redirects=True
    )

    # 4) DELETE THE UNIT
    client.post(
        "/delete_unit",
        data={"unit_id": unit.id},
        follow_redirects=True
    )

    # 5) assert both Unit and its Tasks are gone
    with client.application.app_context():
        assert Unit.query.count() == 0
        assert Task.query.count() == 0
