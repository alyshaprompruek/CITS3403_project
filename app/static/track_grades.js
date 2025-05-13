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
    const score = document.getElementById("scoreInput").value.trim();
    const weight = document.getElementById("weightInput").value.trim();
    const date = document.getElementById("dateInput").value.trim();
    const note = document.getElementById("noteInput").value.trim();
    const type = document.getElementById("assessmentTypeDropdown").value.trim();

    if (!taskName || !score || !weight || !date) {
        alert("All fields except 'Note' are required!");
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
            note: note
        })
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            const newAssessment = {
                task_name: taskName,
                score: score,
                weight: weight,
                date: date,
                note: note,
                type: type
            };
            currentUnit.assessments.push(newAssessment);
            updateView();
            closeAssessmentModal();
        } else {
            alert("Failed to add assessment.");
        }
    })
    .catch(err => {
        console.error("Error adding assessment:", err);
    });
}
