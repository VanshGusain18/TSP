document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("graphCanvas");
  const ctx = canvas.getContext("2d");

  let nodes = [];
  let edges = [];
  let nodeCoords = [];

  function scaleCoordinates(rawNodes) {
    const lats = rawNodes.map((n) => n.y);
    const lons = rawNodes.map((n) => n.x);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    const padding = 40;
    const width = canvas.width - 2 * padding;
    const height = canvas.height - 2 * padding;

    return rawNodes.map((n) => {
      return {
        x: padding + ((n.x - minLon) / (maxLon - minLon)) * width,
        y: padding + ((maxLat - n.y) / (maxLat - minLat)) * height,
      };
    });
  }

  function drawGraph(singlePath = null, pathMap = {}, colorMap = {}) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    edges.forEach(([fromIdx, toIdx]) => {
      let strokeStyle = "rgba(209, 213, 219, 0.4)";
      let lineWidth = 1.5;
      let shadowBlur = 0;

      if (singlePath) {
        const isInPath =
          singlePath.includes(fromIdx) &&
          singlePath.includes(toIdx) &&
          Math.abs(singlePath.indexOf(fromIdx) - singlePath.indexOf(toIdx)) ===
            1;

        if (isInPath) {
          strokeStyle = "#ef4444";
          lineWidth = 4;
          shadowBlur = 10;
        }
      } else {
        for (const metric in pathMap) {
          const path = pathMap[metric];
          const color = colorMap[metric];

          const isInPath =
            path.includes(fromIdx) &&
            path.includes(toIdx) &&
            Math.abs(path.indexOf(fromIdx) - path.indexOf(toIdx)) === 1;

          if (isInPath) {
            strokeStyle = color;
            lineWidth = 3;
            shadowBlur = 6;
            break;
          }
        }
      }

      const from = nodeCoords[fromIdx];
      const to = nodeCoords[toIdx];
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.strokeStyle = strokeStyle;
      ctx.lineWidth = lineWidth;
      ctx.shadowColor = strokeStyle;
      ctx.shadowBlur = shadowBlur;
      ctx.stroke();
    });

    nodeCoords.forEach((node, idx) => {
      ctx.beginPath();
      ctx.arc(node.x, node.y, 10, 0, 2 * Math.PI);
      ctx.fillStyle = "#1f2937";
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const initials = nodes[idx].name
        .split(" ")
        .map((w) => w[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();
      ctx.fillText(initials, node.x, node.y);
    });

    ctx.shadowBlur = 0;
  }

  fetch("/get-graph")
    .then((res) => res.json())
    .then((data) => {
      nodes = data.nodes;
      edges = data.edges;
      nodeCoords = scaleCoordinates(nodes);
      drawGraph();

      const startSelect = document.getElementById("start");
      const goalSelect = document.getElementById("goal");

      nodes.forEach((node) => {
        const opt1 = new Option(node.name, node.name);
        const opt2 = new Option(node.name, node.name);
        startSelect.add(opt1);
        goalSelect.add(opt2);
      });
    });

  document.getElementById("routeForm").addEventListener("submit", (e) => {
    e.preventDefault();

    const start = document.getElementById("start").value;
    const goal = document.getElementById("goal").value;
    const metric = document.getElementById("metric").value;
    const multiMetric = document.getElementById("multiMetric").checked;
    const resultDiv = document.getElementById("result");

    if (start === goal) {
      resultDiv.textContent = "Start and goal nodes must be different.";
      return;
    }

    resultDiv.textContent = "Calculating...";

    const metrics = multiMetric ? ["distance", "time", "fuel"] : [metric];
    const colors = {
      distance: "#ef4444",
      time: "#10b981",
      fuel: "#3b82f6",
    };

    const pathResults = {};
    const pathIndicesMap = {};

    Promise.all(
      metrics.map((m) =>
        fetch(`/path/${m}/${start}/${goal}`)
          .then((res) => res.json())
          .then((data) => {
            if (!data.error) {
              pathResults[m] = data;
              pathIndicesMap[m] = data.path.map((name) =>
                nodes.findIndex((n) => n.name === name)
              );
            }
          })
      )
    )
      .then(() => {
        if (Object.keys(pathResults).length === 0) {
          resultDiv.textContent = "No path found for any metric.";
          drawGraph();
          return;
        }

        resultDiv.innerHTML = "";
        for (const m of metrics) {
          if (pathResults[m]) {
            const d = pathResults[m];
            resultDiv.innerHTML +=
              `<strong>${m.toUpperCase()}:</strong><br>` +
              `Path: ${d.path.join(" → ")}<br>` +
              `Distance: ${d.distance}<br>` +
              `Time: ${d.time}<br>` +
              `Fuel: ${d.fuel}<br><br>`;
          }
        }

        drawGraph(null, pathIndicesMap, colors);

        const legendDiv = document.getElementById("legend");
        if (multiMetric) {
          legendDiv.innerHTML = "";
          for (const m of metrics) {
            if (pathResults[m]) {
              const colorBox = `<span class="legend-color" style="background-color: ${colors[m]}"></span>`;
              const label = `<span>${
                m.charAt(0).toUpperCase() + m.slice(1)
              }</span>`;
              legendDiv.innerHTML += `<div class="legend-item">${colorBox}${label}</div>`;
            }
          }
        } else {
          document.getElementById("legend").innerHTML = "";
        }
      })
      .catch(() => {
        resultDiv.textContent = "Failed to fetch route. Please try again.";
        drawGraph();
      });
  });
});
