function addCourse() {
    const subject = prompt("Enter Course Subject (3-4 uppercase letters):");
    const number = prompt("Enter Course Number:");
    const creditHours = prompt("Enter GPA Credit Hours:");

    // Basic validation
    if (!subject || !number || !creditHours) {
        alert("All fields are required!");
        return;
    }

    if (!/^[A-Z]{3,4}$/.test(subject.trim())) {
        alert("Course subject must be 3 or 4 uppercase letters.");
        return;
    }

    if (isNaN(creditHours) || Number(creditHours) <= 0) {
        alert("GPA Credit Hours must be a valid number greater than 0.");
        return;
    }

    const newCourse = {
        subject: subject.trim(),
        number: number.trim(),
        creditHours: Number(creditHours)
    };

    courses.push(newCourse); // Assuming you have a `courses` array
    updateCourseView(); // Custom function to re-render or show the course
}
