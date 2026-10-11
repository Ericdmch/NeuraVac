const canvas = document.getElementById("lidar-canvas");
const context = canvas.getContext("2d");

/** Draw [x, y] points in metres, joining each point to the next. */
function drawLidarPoints(points) {
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);

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
}
