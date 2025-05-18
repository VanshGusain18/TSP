document.addEventListener("DOMContentLoaded", () => {
  const startSelect = document.getElementById("start");
  const goalSelect = document.getElementById("goal");
  const form = document.getElementById("routeForm");
  const resultDiv = document.getElementById("result");

  // Fetch graph data to populate nodes dropdown
  fetch("/get-graph")
    .then((res) => res.json())
    .then((data) => {
      // We don't get node names directly, so let's assume node names are A-J
      // Adjust if your database node names differ
      const nodeNames = "ABCDEFGHIJ".split("");

      nodeNames.forEach((name) => {
        const option1 = document.createElement("option");
        option1.value = name;
        option1.textContent = name;
        startSelect.appendChild(option1);

        const option2 = document.createElement("option");
        option2.value = name;
        option2.textContent = name;
        goalSelect.appendChild(option2);
      });
    })
    .catch(() => {
      alert("Failed to load nodes");
    });

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const start = startSelect.value;
    const goal = goalSelect.value;
    const metric = document.getElementById("metric").value;

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
        } else {
          resultDiv.innerHTML =
            `<strong>Path:</strong> ${data.path.join(" → ")}\n` +
            `<strong>Distance:</strong> ${data.distance}\n` +
            `<strong>Time:</strong> ${data.time}\n` +
            `<strong>Fuel:</strong> ${data.fuel}`;
        }
      })
      .catch(() => {
        resultDiv.textContent = "Failed to fetch route. Please try again.";
      });
  });
});
