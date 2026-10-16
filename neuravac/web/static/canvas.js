const canvas = document.getElementById("lidar-canvas");
const context = canvas.getContext("2d");

/** Draw a screen-aligned marker at the centre of the lidar view. */
function drawRoombaIcon() {
    const x = canvas.width / 2;
    const y = canvas.height / 2;
    // At the current 80 px/m scale, 10 cm is about 8 px from centre.
    // Keep the body to 6 px across so nearby returns remain visible.
    const radius = 12;

    context.beginPath();
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.fillStyle = "#f28c28";
    context.fill();

    // The arrow points to the top of the screen regardless of robot heading.
    context.beginPath();
    context.moveTo(x, y - radius + 2);
    context.lineTo(x - 6, y + 6);
    context.lineTo(x, y + 1);
    context.lineTo(x + 6, y + 6);
    context.closePath();
    context.fillStyle = "#ffffff";
    context.fill();
}

/** Draw [x, y] points in metres, joining each point to the next. */
function drawLidarPoints(points) {
    
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    drawRoombaIcon();

    if (!Array.isArray(points) || points.length === 0) {
        return;
    }

    // Map a centered 10 m by 8 m room area to the canvas, preserving scale.
    const pixelsPerMetre = Math.min(canvas.width / 10, canvas.height / 8);
    const toCanvasPoint = ([x, y]) => ({
        x: canvas.width / 2 + x * pixelsPerMetre,
        y: canvas.height / 2 - y * pixelsPerMetre
    });

    const firstPoint = toCanvasPoint(points[0]);
    context.beginPath();
    context.moveTo(firstPoint.x, firstPoint.y);

    for (let i = 1; i < points.length; i += 1) {
        const point = toCanvasPoint(points[i]);
        context.lineTo(point.x, point.y);
    }

    context.strokeStyle = "#000000";
    context.lineWidth = 2;
    context.stroke();
    return "plotted";
}

// Show the robot marker even before the first lidar update arrives.
drawLidarPoints([]);
