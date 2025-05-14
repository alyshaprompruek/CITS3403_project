from datetime import date
from app.models import Unit, Task, User

def calculate_unit_score(tasks):
    score_sum = 0
    weight_sum = 0
    for task in tasks:
        if task.grade is not None and task.weighting is not None:
            score_sum += task.grade * (task.weighting / 100)
            weight_sum += task.weighting
            
    # Cap weight_sum at 100% to avoid over-calculation
    weight_sum = min(weight_sum, 100)

    # Calculate the average grade
    average_grade = round(score_sum / (weight_sum / 100), 2) if weight_sum > 0 else 0

    # Calculate remaining weight
    remaining_weight = round(100 - weight_sum, 2)

    return average_grade, remaining_weight
    return round(score_sum, 2), round(100 - weight_sum, 2)

def calculate_recommendation(target_score, current_score, remaining_weight):
    if remaining_weight <= 0:
        return None  
    required_score = (target_score - current_score) / (remaining_weight / 100)
    return round(required_score, 2)

def calculate_user_statistics(user_id):
    user = User.query.get(user_id)
    units = Unit.query.filter_by(user_id=user_id).all()

    unit_scores = []
    ranked_units = []
    total_score = 0
    count = 0
    top_unit = None
    top_score = -1
    recommendations = []
    upcoming_tasks = []

    for unit in units:
        tasks = Task.query.filter_by(unit_id=unit.id).all()
        unit_score, remaining_weight = calculate_unit_score(tasks)

        if unit_score > top_score:
            top_score = unit_score
            top_unit = unit.unit_code

        if unit_score > 0:
            total_score += unit_score
            count += 1

        unit.grade = unit_score if unit_score > 0 else None
        ranked_units.append((unit.unit_code, unit_score))

        
        recommendation = None
        if unit.target_score:
            recommendation = calculate_recommendation(unit.target_score, unit_score, remaining_weight)
        recommendations.append({
            "unit_code": unit.unit_code,
            "current_score": unit_score,
            "target": unit.target_score,
            "remaining_weight": remaining_weight,
            "required_score": recommendation
        })

        
        today_str = date.today().isoformat()
        for task in tasks:
            if task.date and task.date >= today_str:
                upcoming_tasks.append({
                    "unit_code": unit.unit_code,
                    "task_name": task.task_name,
                    "date": task.date,
                    "notes": task.notes or "",
                    "grade": task.grade
                })

        unit_scores.append({
            "unit": unit,
            "score": unit_score,
            "remaining_weight": remaining_weight
        })

    wam = round(total_score / count, 2) if count > 0 else None

    return {
        "wam": wam,
        "gpa": None,  
        "top_unit": top_unit,
        "unit_scores": unit_scores,
        "recommendations": recommendations,
        "ranked_units": sorted(ranked_units, key=lambda x: x[1], reverse=True),
        "upcoming_tasks": upcoming_tasks
    }
