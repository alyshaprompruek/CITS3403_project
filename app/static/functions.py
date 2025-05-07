def calculate_gpa(grades):
    total = 0
    for grade in grades:
        if grade >= 80:
            total += 7
        elif grade >= 70:
            total += 6
        elif grade >= 60:
            total += 5
        elif grade >= 50:
            total += 4
        #else add nothing
    
    return total / len(grades) if grades else 0