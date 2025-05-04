const mockData = {
    admin: {
      units: [
        {
          unit_id: "u1",
          unit_name: "CITS3403",
          target_score: 80,
          assessments: [
            { task_name: "Assignment 1", score: "78", weight: "20%", date: "2025-04-01", note: "Good effort" },
            { task_name: "Quiz", score: "85", weight: "10%", date: "2025-04-10", note: "" },
            { task_name: "Final Exam", score: "/", weight: "70%", date: "2025-06-01", note: "Yet to complete" }
          ]
        }
      ]
    }
  };
  

// track_grades.js

let currentUser = { name: "admin" };
let currentUnit = null;
let lineChart, pieChart;

// get mock data form mockData.js
window.onload = () => {
    currentUser.units = mockData.admin.units;
    currentUnit = currentUser.units[0];
    updateView();
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
  const pieCtx = document.getElementById("pieChart").getContext("2d");

  const lineData = assessments.filter(a => a.score !== "/" && !isNaN(Number(a.score)))
    .map(a => ({ x: a.date, y: Number(a.score) }));

  const pieData = assessments.map(a => ({
    label: a.task_name,
    value: parseFloat(a.weight.replace("%", ""))
  }));

  if (lineChart) lineChart.destroy();
  if (pieChart) pieChart.destroy();

  lineChart = new Chart(lineCtx, {
    type: 'line',
    data: {
      datasets: [{
        label: "Score Over Time",
        data: lineData,
        fill: false,
        borderColor: 'blue'
      }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                onClick: () => {},  // disable clicking
                labels: {
                    color: '#000',
                    boxWidth: 12,
                    font: { weight: 'bold' }
                }
            }
        },
        scales: { x: { type: 'time', time: { unit: 'day' } } }
    }
  });

  pieChart = new Chart(pieCtx, {
    type: 'pie',
    data: {
      labels: pieData.map(p => p.label),
      datasets: [{
        data: pieData.map(p => p.value),
        backgroundColor: ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0"]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom',
          onClick: () => {}, // disable clicking
          labels: {
            color: '#000',
            font: { size: 12 }
          }
        }
      }
    }
  });
}
