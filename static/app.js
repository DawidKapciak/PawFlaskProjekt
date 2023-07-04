$(document).ready(function () {
  const ctx = document.getElementById("apiKeyChart").getContext("2d");

  const apiKeyChart = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [{ label: "Żądania",  }],
    },
    options: {
      scales: {
        y: {
          ticks: {
            stepSize: 1,
            callback: function (value, index, values) {
              if (Number.isInteger(value)) {
                return value;
              }
              return '';
            },
          },
        },
      },
      borderWidth: 6,
      borderColor: ['rgb(255,0,0)',],
    },
  });

  function addData(label, data) {
    apiKeyChart.data.labels.push(label);
    apiKeyChart.data.datasets.forEach((dataset) => {
      dataset.data.push(data);
    });
    apiKeyChart.update();
  }

  function removeFirst() {
    apiKeyChart.data.labels.splice(0, 1);
    apiKeyChart.data.datasets.forEach((dataset) => {
      dataset.data.shift();
    });
  }

  const MAX_DATA_COUNT = 10;
  const socket = io.connect();

  socket.on("updateData", function (msg) {
    console.log("Otrzymane dane: " + msg.date + " : " + msg.value);

    if (apiKeyChart.data.labels.length > MAX_DATA_COUNT) {
      removeFirst();
    }
    addData(msg.date, msg.value);
  });
});