document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("graphCanvas");
  const ctx = canvas.getContext("2d");

  let nodes = [];
  let edges = [];
  let nodeCoords = []; // screen coords

  // Transform lat/lon to canvas coordinates
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
        y: padding + ((maxLat - n.y) / (maxLat - minLat)) * height, // flip y
      };
    });
  }

  function drawGraph(path = []) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw edges
    edges.forEach(([fromIdx, toIdx]) => {
      const from = nodeCoords[fromIdx];
      const to = nodeCoords[toIdx];
      const isInPath =
        path.includes(fromIdx) &&
        path.includes(toIdx) &&
        Math.abs(path.indexOf(fromIdx) - path.indexOf(toIdx)) === 1;
      ctx.strokeStyle = isInPath ? "red" : "#999";
      ctx.lineWidth = isInPath ? 3 : 1;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    });

    // Draw nodes
    nodeCoords.forEach((node, idx) => {
      ctx.beginPath();
      ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI);
      ctx.fillStyle = path.includes(idx) ? "#007bff" : "#333";
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "12px Arial";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String.fromCharCode(65 + idx), node.x, node.y);
    });
  }

  fetch("/get-graph")
    .then((res) => res.json())
    .then((data) => {
      nodes = data.nodes;
      edges = data.edges;
      nodeCoords = scaleCoordinates(nodes);
      drawGraph();

      // populate selects (replace old logic)
      const nodeNames = nodes.map((_, i) => String.fromCharCode(65 + i));
      const startSelect = document.getElementById("start");
      const goalSelect = document.getElementById("goal");

      nodeNames.forEach((name) => {
        const opt1 = new Option(name, name);
        const opt2 = new Option(name, name);
        startSelect.add(opt1);
        goalSelect.add(opt2);
      });
    });

  // Hook to form submission
  document.getElementById("routeForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const start = document.getElementById("start").value;
    const goal = document.getElementById("goal").value;
    const metric = document.getElementById("metric").value;
    const resultDiv = document.getElementById("result");

    if (start === goal) {
      resultDiv.textContent = "Start and goal nodes must be different.";
      return;
    }

    resultDiv.textContent = "Calculating...";

    fetch(`/path/${metric}/${start}/${goal}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          resultDiv.textContent = `Error: ${data.error}`;
          drawGraph(); // reset graph
        } else {
          resultDiv.innerHTML =
            `<strong>Path:</strong> ${data.path.join(" → ")}\n` +
            `<strong>Distance:</strong> ${data.distance}\n` +
            `<strong>Time:</strong> ${data.time}\n` +
            `<strong>Fuel:</strong> ${data.fuel}`;

          // Convert path from node letters to indices (A -> 0, B -> 1, ...)
          const pathIndices = data.path.map((ch) => ch.charCodeAt(0) - 65);
          drawGraph(pathIndices);
        }
      })
      .catch(() => {
        resultDiv.textContent = "Failed to fetch route. Please try again.";
        drawGraph();
      });
  });
});
