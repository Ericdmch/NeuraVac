const serialMonitorInput = document.querySelector("#serial-monitor-in input");
const serialMonitorOutput = document.getElementById("serial-monitor-out");
const serialMonitorStatus = document.getElementById("serial-monitor-status");

function setSerialMonitorConnection(connected) {
    serialMonitorStatus.classList.toggle("connected", connected);
    serialMonitorStatus.classList.toggle("disconnected", !connected);
    serialMonitorStatus.title = connected ? "Serial connected" : "Serial disconnected";
    serialMonitorInput.disabled = !connected;
}

function appendSerialMonitorMessage(message) {
    const line = document.createElement("div");
    line.textContent = message;
    serialMonitorOutput.appendChild(line);
    serialMonitorOutput.scrollTop = serialMonitorOutput.scrollHeight;
}

async function checkSerialMonitorConnection() {
    try {
        const response = await fetch("/api/serial-monitor/status");
        const result = await response.json();
        setSerialMonitorConnection(result.connected === true);
    } catch (error) {
        setSerialMonitorConnection(false);
    }
}

async function readSerialMonitorMessages() {
    try {
        const response = await fetch("/api/serial-monitor/messages");
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || "Unable to read serial data");
        }

        setSerialMonitorConnection(true);
        result.messages.forEach(appendSerialMonitorMessage);
    } catch (error) {
        setSerialMonitorConnection(false);
    }
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
        setSerialMonitorConnection(false);
        console.log(error.message);
    }
});

checkSerialMonitorConnection();
setInterval(readSerialMonitorMessages, 100);
