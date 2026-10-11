const serialMonitorInput = document.querySelector("#serial-monitor-in input");
const serialMonitorOutput = document.getElementById("serial-monitor-out");
const serialMonitorStatus = document.getElementById("serial-monitor-status");

function appendSerialMonitorMessage(message) {
    const line = document.createElement("div");
    line.textContent = message;
    serialMonitorOutput.appendChild(line);
    serialMonitorOutput.scrollTop = serialMonitorOutput.scrollHeight;
}

serialMonitorInput.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter" || !serialMonitorInput.value.trim()) {
        return;
    }

    const message = serialMonitorInput.value;
    serialMonitorInput.value = "";

    try {
        const response = await fetch("/api/serial-monitor", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message}),
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || "Unable to send message");
        }
        appendSerialMonitorMessage(result.message);
    } catch (error) {
        console.log( error.message );
    }
});
