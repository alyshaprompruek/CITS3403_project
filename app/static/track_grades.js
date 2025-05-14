// const mockData = {
//     admin: {
//       units: [
//         {
//           unit_id: "u1",
//           unit_name: "CITS3403",
//           target_score: 80,
//           assessments: [
//             { task_name: "Assignment 1", score: "78", weight: "20%", date: "2025-04-01", note: "Good effort" },
//             { task_name: "Quiz", score: "85", weight: "10%", date: "2025-04-10", note: "" },
//             { task_name: "Final Exam", score: "/", weight: "70%", date: "2025-06-01", note: "Yet to complete" }
//           ]
//         }
//       ]
//     }
//   };
  

// track_grades.js

let currentUser = { name: "admin" };
let currentUnit = null;
let lineChart, pieChart;

window.onload = () => {
    fetch("/api/units")
        .then(response => response.json())
        .then(data => {
            currentUser.units = data.units;
            currentUnit = currentUser.units.length > 0 ? currentUser.units[0] : null;
            updateView();
        })
        .catch(error => {
            console.error("Failed to load units:", error);
        });
};

function selectUnit(unit) {
  currentUnit = unit;
  updateView();
}

function updateView() {
    const unitList = document.getElementById("unitList");
    const noUnitBox = document.getElementById("noUnitBox");
    const selectUnitBox = document.getElementById("selectUnitBox");
    const courseContent = document.getElementById("courseContent");
    const currentTitle = document.getElementById("currentUnitTitle");
    const tableBody = document.querySelector("#assessmentTable tbody");
    const tableHead = document.querySelector("#assessmentTable thead tr");

    // Clear the unit list
    unitList.innerHTML = "";

    // Populate the unit list
    currentUser.units.forEach(unit => {
        const btn = document.createElement("button");
        btn.textContent = unit.unit_name;
        btn.className = "list-group-item list-group-item-action";
        btn.onclick = () => selectUnit(unit);
        unitList.appendChild(btn);
    });

    // Handle visibility of messages and content
    if (currentUser.units.length === 0) {
        noUnitBox.classList.remove("hidden");
        selectUnitBox.classList.add("hidden");
        courseContent.classList.add("hidden");
    } else if (!currentUnit) {
        noUnitBox.classList.add("hidden");
        selectUnitBox.classList.remove("hidden");
        courseContent.classList.add("hidden");
    } else {
        noUnitBox.classList.add("hidden");
        selectUnitBox.classList.add("hidden");
        courseContent.classList.remove("hidden");
        currentTitle.textContent = currentUnit.unit_name;

        // Add Actions header if not present
        if (!tableHead.querySelector("th.actions-header")) {
            const actionsTh = document.createElement("th");
            actionsTh.textContent = "Actions";
            actionsTh.className = "actions-header";
            tableHead.appendChild(actionsTh);
        }

        // Populate the assessment table
        tableBody.innerHTML = "";
        currentUnit.assessments.forEach(a => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${a.task_name}</td>
                <td>${a.score}</td>
                <td>${a.weight}</td>
                <td>${a.date}</td>
                <td>${a.note}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-2" onclick='openEditAssessmentModal(currentUnit.assessments[${currentUnit.assessments.indexOf(a)}])'>Edit</button>
                    <button class="btn btn-sm btn-outline-danger" onclick='deleteAssessment("${a.task_name}")'>Delete</button>
                </td>
            `;
            tableBody.appendChild(row);
        });

        // Render charts
        renderCharts(currentUnit.assessments);
    }
}

function renderCharts(assessments) {
    const lineCtx = document.getElementById("lineChart").getContext("2d");

    const sortedAssessments = [...assessments].sort((a, b) => {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        if (dateA.getTime() !== dateB.getTime()) {
            return dateA - dateB;
        }
        return 0; // Placeholder: add secondary sorting here if needed
    });

    const lineData = sortedAssessments
        .filter(a => a.score !== "/" && !isNaN(Number(a.score)))
        .map(a => ({ x: a.date, y: Number(a.score) }));

    const gradeRangeMap = {
        80: [80, 100],
        70: [70, 80],
        60: [60, 70],
        50: [50, 60]
    };

    let gradeRange = null;
    if (currentUnit.target_score in gradeRangeMap) {
        gradeRange = gradeRangeMap[currentUnit.target_score];
        console.log("Target grade range:", gradeRange);
    }

    const annotations = gradeRange ? {
        targetZone: {
            type: 'box',
            yMin: gradeRange[0],
            yMax: gradeRange[1],
            backgroundColor: 'rgba(173, 223, 133, 0.34)',
            borderWidth: 0,
        }
    } : {};

    if (lineChart) lineChart.destroy();

    lineChart = new Chart(lineCtx, {
    type: 'line',
    data: {
        datasets: [{
            label: "Score Over Time",
            data: lineData,
            borderColor: '#4CAF50',
            backgroundColor: '#A5D6A7',
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                labels: {
                    color: '#000',
                    boxWidth: 12,
                    font: { weight: 'bold' }
                }
            },
            annotation: {
                annotations: annotations
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'day'
                }
            },
            y: {
                beginAtZero: true,
                max: 100
            }
        },
        layout: {
            padding: {
                left: 20,
                right: 20,
                top: 20,
                bottom: 20
            }
        },
    },
    plugins: [{
        id: 'custom_canvas_background_color',
        beforeDraw: (chart) => {
            const ctx = chart.canvas.getContext('2d');
            ctx.save();
            ctx.globalCompositeOperation = 'destination-over';
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, chart.width, chart.height);
            ctx.restore();
        }
    }]
});


}

function openUnitModal() {
    document.getElementById("unitModal").classList.remove("hidden");
}

function closeUnitModal() {
    document.getElementById("unitModal").classList.add("hidden");
}

function confirmAddUnit() {
    const name = document.getElementById("unitNameInput").value.trim();
    if (!name) {
        alert("Unit name cannot be empty.");
        return;
    }

    fetch("/api/add_unit_direct", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            unit_name: name,
            target_score: 80
        })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            const unit = {
                unit_id: result.unit_id,
                unit_name: name,
                target_score: 80,
                assessments: []
            };
            currentUser.units.push(unit);
            selectUnit(unit);
            updateView();
            closeUnitModal();
        } else {
            alert("Failed to add unit.");
        }
    })
    .catch(err => {
        console.error("Error adding unit:", err);
    });
}

function openAssessmentModal() {
    document.getElementById("assessmentModal").classList.remove("hidden");
}

function closeAssessmentModal() {
    document.getElementById("assessmentModal").classList.add("hidden");
}

function confirmAddAssessment() {
    const taskName = document.getElementById("taskNameInput").value.trim();
    const score = parseFloat(document.getElementById("scoreInput").value.trim());
    const weight = document.getElementById("weightInput").value.trim();
    const date = document.getElementById("dateInput").value.trim();
    const note = document.getElementById("noteInput").value.trim();
    const type = document.getElementById("assessmentTypeDropdown").value.trim();

    if (!taskName || isNaN(score) || !weight || !date) {
        alert("All fields except 'Note' are required!");
        return;
    }

    // Validate that the score does not exceed 100
    if (score > 100) {
        alert("Score cannot exceed 100.");
        return;
    }

    fetch("/api/add_assessment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            unit_id: currentUnit.unit_id,
            task_name: taskName,
            score: score,
            weight: weight,
            date: date,
            note: note,
            type: type
        })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            const newAssessment = {
                task_name: taskName,
                score: score,
                weight: `${weight}%`,
                date: date,
                note: note,
                type: type
            };
            currentUnit.assessments.push(newAssessment);
            updateView();
            closeAssessmentModal();
        } else {
            alert(result.error || "Failed to add assessment.");
        }
    })
    .catch(err => {
        console.error("Error adding assessment:", err);
    });
}

function openEditAssessmentModal(task) {
    document.getElementById("editTaskNameInput").value = task.task_name;
    document.getElementById("editAssessmentTypeDropdown").value = task.type || "other"; // Use the type field from the backend
    document.getElementById("editScoreInput").value = task.score;
    document.getElementById("editWeightInput").value = task.weight.replace('%', ''); // Remove the percentage symbol
    document.getElementById("editDateInput").value = task.date;
    document.getElementById("editNoteInput").value = task.note || ""; // Default to an empty string if note is missing
    document.getElementById("editAssessmentModal").classList.remove("hidden");

    // Optional: Store a reference to the task to be updated later
    window.assessmentToEdit = task;
}

function closeEditAssessmentModal() {
    document.getElementById("editAssessmentModal").classList.add("hidden");
}

function confirmEditAssessment() {
    const updatedTask = {
        task_name: document.getElementById("editTaskNameInput").value.trim(),
        type: document.getElementById("editAssessmentTypeDropdown").value.trim(),
        score: document.getElementById("editScoreInput").value.trim(),
        weight: document.getElementById("editWeightInput").value.trim(),
        date: document.getElementById("editDateInput").value.trim(),
        note: document.getElementById("editNoteInput").value.trim()
    };

    fetch("/api/edit_assessment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            unit_id: currentUnit.unit_id,
            original_task_name: window.assessmentToEdit.task_name,
            task_name: updatedTask.task_name,
            type: updatedTask.type,
            score: updatedTask.score,
            weight: updatedTask.weight,
            date: updatedTask.date,
            note: updatedTask.note
        })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            Object.assign(window.assessmentToEdit, updatedTask);
            updateView();
            closeEditAssessmentModal();
        } else {
            alert("Failed to update assessment.");
        }
    })
    .catch(err => {
        console.error("Error updating assessment:", err);
    });
}

function deleteAssessment(taskName) {
    if (!confirm("Are you sure you want to delete this assessment?")) {
        return;
    }

    fetch("/api/delete_assessment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            unit_id: currentUnit.unit_id,
            task_name: taskName
        })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            // Remove the assessment from the frontend
            currentUnit.assessments = currentUnit.assessments.filter(a => a.task_name !== taskName);
            updateView();
        } else {
            alert(result.error || "Failed to delete assessment.");
        }
    })
    .catch(err => {
        console.error("Error deleting assessment:", err);
        alert("An unexpected error occurred. Please try again.");
    });
}
