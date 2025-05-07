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

function simulateAddUnit() {
  const name = prompt("unit name:", "New Unit");
  if (!name || name.trim() === "") return;
  const unit = {
    unit_id: "u" + (currentUser.units.length + 1),
    unit_name: name.trim(),
    target_score: 80,
    assessments: []
  };
  currentUser.units.push(unit);
  selectUnit(unit);
  updateView();
}

function selectUnit(unit) {
  currentUnit = unit;
  updateView();
}

function updateView() {
  const unitList = document.getElementById("unitList");
  const noUnitBox = document.getElementById("noUnitBox");
  const courseContent = document.getElementById("courseContent");
  const currentTitle = document.getElementById("currentUnitTitle");
  const tableBody = document.querySelector("#assessmentTable tbody");

  unitList.innerHTML = "";
  currentUser.units.forEach(unit => {
    const btn = document.createElement("button");
    btn.textContent = unit.unit_name;
    btn.onclick = () => selectUnit(unit);
    unitList.appendChild(btn);
  });

  if (!currentUnit) {
    noUnitBox.classList.remove("hidden");
    courseContent.classList.add("hidden");
  } else {
    noUnitBox.classList.add("hidden");
    courseContent.classList.remove("hidden");
    currentTitle.textContent = currentUnit.unit_name;

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

    renderCharts(currentUnit.assessments);
  }
}

function renderCharts(assessments) {
    const lineCtx = document.getElementById("lineChart").getContext("2d");

    const lineData = assessments.filter(a => a.score !== "/" && !isNaN(Number(a.score)))
        .map(a => ({ x: a.date, y: Number(a.score) }));

    if (lineChart) lineChart.destroy();

    lineChart = new Chart(lineCtx, {
    type: 'line',
    data: {
        datasets: [{
            label: "Score Over Time",
            data: lineData,
            borderColor: '#4CAF50', // green
            backgroundColor: '#A5D6A7', // optional, if you want filled points or area under the line
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
            }
        },
        scales: {
            x: {
                type: 'time',
                time: {
                    unit: 'day'
                }
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
    
    }
});

}

function addAssessment() {
    const taskName = prompt("Enter Task Name:");
    const score = prompt("Enter Score (e.g., 85):");
    const weight = prompt("Enter Weight (e.g., 20%):");
    const date = prompt("Enter Date (YYYY-MM-DD):");
    const note = prompt("Enter Note (optional):");

    if (!taskName || !score || !weight || !date) {
        alert("All fields except 'Note' are required!");
        return;
    }

    const newAssessment = {
        task_name: taskName.trim(),
        score: score.trim(),
        weight: weight.trim(),
        date: date.trim(),
        note: note ? note.trim() : ""
    };

    currentUnit.assessments.push(newAssessment);
    updateView(); // Refresh the view to include the new assessment
}
