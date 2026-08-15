// Front-end do dashboard: consome a API Flask (/api/dashboard-data) e
// desenha os gráficos com Chart.js.

async function carregarDashboard() {
  const resposta = await fetch("/api/dashboard-data");
  if (!resposta.ok) {
    console.error("Falha ao buscar dados do dashboard", resposta.status);
    return;
  }
  const dados = await resposta.json();

  // KPI de custo médio por KM
  document.getElementById("kpiCustoKm").textContent =
    "R$ " + dados.custo_medio_km.toFixed(2);

  // Gráfico de linha: Faturamento vs Custo Total
  new Chart(document.getElementById("graficoFaturamento"), {
    type: "line",
    data: {
      labels: dados.labels,
      datasets: [
        {
          label: "Faturamento (R$)",
          data: dados.faturamento,
          borderColor: "#2dd4bf",
          backgroundColor: "rgba(45,212,191,0.15)",
          tension: 0.3,
        },
        {
          label: "Custo Total (R$)",
          data: dados.custo_total,
          borderColor: "#f59e0b",
          backgroundColor: "rgba(245,158,11,0.15)",
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#93a2c7" } } },
      scales: {
        x: { ticks: { color: "#93a2c7" }, grid: { color: "#263559" } },
        y: { ticks: { color: "#93a2c7" }, grid: { color: "#263559" } },
      },
    },
  });

  // Gráfico de barras: Volume de carga (toneladas)
  new Chart(document.getElementById("graficoVolume"), {
    type: "bar",
    data: {
      labels: dados.labels,
      datasets: [
        {
          label: "Toneladas",
          data: dados.volume_tons,
          backgroundColor: "#2dd4bf",
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#93a2c7" }, grid: { display: false } },
        y: { ticks: { color: "#93a2c7" }, grid: { color: "#263559" } },
      },
    },
  });
}

document.addEventListener("DOMContentLoaded", carregarDashboard);
