from datetime import date
from app.models import Unit, Task, User  # Assuming these are your models

def calculate_gpa(grades):
    print(grades)
    """
    Calculates GPA based on a list of grades.

    Args:
        grades: A list of numerical grades.

    Returns:
        The GPA as a float, or 0 if the list is empty.
    """
    total = 0
    count = 0
    for grade in grades:
        if grade is not None:
            count += 1

        if grade >= 80:
            total += 7
        elif grade >= 70:
            total += 6
        elif grade >= 60:
            total += 5
        elif grade >= 50:
            total += 4
        # else:  # No need for an else: pass is implicit.  More concise.
    
    return 0 if count == 0 else total / count


def calculate_unit_score(tasks):
    """
    Calculates the weighted score and remaining weight for a unit based on its tasks.

    Args:
        tasks: A list of Task objects.

    Returns:
        A tuple containing the rounded weighted score and the rounded remaining weight.
    """
    score_sum = 0
    weight_sum = 0
    for task in tasks:
        if task.grade is not None and task.weighting is not None:
            score_sum += task.grade * (task.weighting / 100)
            weight_sum += task.weighting
    return round((0 if weight_sum == 0 else score_sum/ weight_sum) * 100, 1), round(100 - weight_sum, 1)


def calculate_required_score(target_score, current_score, remaining_weight):
    """
    Calculates the required score to achieve the target score.

    Args:
        target_score: The target score for the unit.
        current_score: The current score achieved.
        remaining_weight: The remaining weight of the unit.

    Returns:
        The required score, rounded to 2 decimal places, or None if remaining_weight is 0.
    """
    if remaining_weight <= 0:
        return None
    current_total = current_score * (1 - remaining_weight / 100)
    target_total = target_score
    if target_total - current_total > 0:
        return round(((target_total - current_total) * 100)/remaining_weight,2)
    else:
        return 0


def calculate_user_statistics(user):
    """
    Calculates and returns various statistics for a user, including WAM, GPA, and unit-specific data.

    Args:
        user

    Returns:
        A dictionary containing the calculated statistics.
    """
    units = Unit.query.filter_by(user_id=user.student_id).all() # Assuming Unit.query.filter_by exists

    unit_scores = []
    ranked_units = []
    top_unit = None
    top_score = -1
    recommendations = []
    upcoming_tasks = []
    all_grades = []  # List to store all unit grades for overall GPA calculation
    count = 0

    for unit in units:
        tasks = Task.query.filter_by(unit_id=unit.id).all() # Assuming Task.query.filter_by exists
        unit_score, remaining_weight = calculate_unit_score(tasks)

        if unit_score > top_score:
            top_score = unit_score
            top_unit = unit.unit_code

        unit.grade = unit_score if unit_score > 0 else None
        ranked_units.append((unit.unit_code, unit_score))
        
        if unit_score:
            all_grades.append(unit_score) # add grades for overall GPA
            count += 1

        if unit.target_score:
            required_score = calculate_required_score(unit.target_score, unit_score, remaining_weight)
        else:
            required_score = None
        
        recommendations.append({
            "unit_id":unit.id,
            "unit_code": unit.unit_code,
            "current_score": unit_score,
            "target": unit.target_score,
            "remaining_weight": remaining_weight,
            "required_score": required_score,
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
            "remaining_weight": remaining_weight,
        })

    wam = round(sum(all_grades) / len(all_grades), 2) if len(all_grades) > 0 else None
    overall_gpa = calculate_gpa(all_grades) # Calculate overall GPA

    return {
        "wam": wam,
        "gpa": overall_gpa,  # Use the calculated overall GPA
        "top_unit": top_unit,
        "unit_scores": unit_scores,
        "recommendations": recommendations,
        "ranked_units": sorted(ranked_units, key=lambda x: x[1], reverse=True),
        "upcoming_tasks": upcoming_tasks
    }
