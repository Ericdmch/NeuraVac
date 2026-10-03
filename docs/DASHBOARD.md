# NeuraVac mission dashboard

The React/TypeScript dashboard lives in `dashboard/frontend`. It builds to static assets for the Pi and displays only telemetry received from the backend. There is no built-in sample mission or fabricated offline data.

## Local development

Run the backend on `127.0.0.1:8000`, then:

```sh
cd dashboard/frontend
npm ci
npm run dev
```

Open the local URL printed by Vite. Its development server proxies `/api` and `/ws` to the backend. The development server binds to localhost by default.

```sh
npm run lint
npm test
npm run build
```

The production output is `dashboard/frontend/dist`. Serve those files through the backend or a same-origin reverse proxy that also routes `/api/*` and `/ws`. Vite's development proxy is **not** part of the production bundle. `npm run preview` serves the built files for inspection; it does not provide a production API proxy. Keep API and UI on the same origin. No external fonts, CDN scripts, or asset services are required.

## Telemetry contract

`GET /api/state` and each `/ws` message supply the same JSON snapshot:

```json
{
  "mode": "simulation",
  "mission_id": "mission-identifier",
  "state": "IDLE",
  "battery_percent": 86,
  "connected": true,
  "safety": { "safe": true, "reasons": [], "latched": false },
  "cloud": { "status": "offline", "model": null, "latency_ms": null, "request_id": null },
  "pose": { "x": 1, "y": 1, "yaw": 0 },
  "world": {
    "width": 8, "height": 6, "origin": { "x": 0, "y": 0, "yaw": 0 },
    "objects": [], "regions": [], "obstacles": []
  },
  "path": [],
  "metrics": {},
  "attempts": [],
  "events": [],
  "self_test": { "status": "passed", "checks": {} }
}
```

`mode`, nonempty `state`, and boolean `connected` identify a snapshot. Other sections and observation fields are optional. Explicit null optional metadata is treated as absent. Missing numbers render as an em dash. Coordinates are map-frame meters and yaw is radians. `world.origin` supplies the OccupancyGrid origin as `{x, y, yaw}`; an omitted origin defaults to `(0, 0, 0)` for standalone simulation. Projection first subtracts that origin, then applies its inverse rotation, then inverts the grid-local Y axis for SVG display. Negative map-frame robot, hazard, region, and path coordinates are valid inside the resulting grid bounds. Robot heading is relative to grid yaw. Nonfinite or out-of-bounds coordinates are not drawn. Supporting a rotated map in the display does not imply that a backend semantic layer supports rotated OccupancyGrid origins. A world needs positive width and height to render a map. Floor objects carry `id`, `class_name`, `position`, optional `confidence`, `traversable`, and `vacuumable`. Cleaning regions carry `id`, `position`, optional `debris_score`, `confidence`, `cleaned`, and `reachable`. Obstacles carry `id`, `x`, `y`, and nonnegative `radius`.

Metrics are `initial_debris_score`, `current_debris_score`, `cleanliness_percent`, `coverage_percent`, `regions_remaining`, `successful_passes`, and `retried_passes`. The dashboard displays the backend's estimate and does not recompute coverage, infer success, or count unreachable targets as cleaned. `coverage_percent` is labelled **Target coverage**: the fraction of cleaning targets verified, not whole-floor geometric coverage. Attempt observations use `region_id`, `before_score`, `after_score`, `improvement`, `pass_number`, `success`, and `duration_s`. Improvement remains unreported if the backend omits it. Scores are rendered as scores, without assuming a percentage scale.

Events use `event`, `timestamp`, and optional structured `data`. Decision, plan, reasoning, cloud, and rejection events appear in the reasoning trail. The activity panel shows the last eight events; the decision and observation panels show the last three relevant records. Numeric timestamps are displayed as reported seconds, without assuming an epoch. ISO timestamps display local wall time.

Cloud status, model, latency, and request ID come from actual backend reports. `offline`, `disabled`, `fallback`, `not_configured`, `unavailable`, and `deterministic` statuses explicitly identify offline deterministic planning. Simulation mode itself does not imply a cloud connection. Missing cloud metadata is labelled "Not reported" and never replaced with a model or latency claim.

## Connection and control behavior

The page opens a same-origin WebSocket and polls every 2.5 seconds as a fallback. Socket reconnects use exponential backoff from one second up to thirty seconds, resetting after a valid snapshot. HTTP telemetry requests time out after four seconds. A snapshot is stale after six seconds without a valid update; the last received data stays visible with an explicit stale banner. Start, pause, resume, reset, and simulated chair mutation are disabled while readings are stale or a command is pending. Start and resume additionally require a connected base, affirmative safety clearance, and no latched stop. Start is available in IDLE or COMPLETE; reset is available only in FAULT, and the backend verifies that all sensors are healthy before clearing a latch. The backend remains authoritative and must independently validate all requests.

Mission controls send bodyless POST requests to:

- `/api/mission/start`
- `/api/mission/pause`
- `/api/mission/resume`
- `/api/mission/reset`
- `/api/mission/estop`
- `/api/demo/move-chair` (simulation mode only)

Commands time out after eight seconds. Failed, rejected, or unconfirmed delivery is shown without optimistic mission changes. Emergency stop can be sent even with missing or unsafe telemetry, and can interrupt a pending UI command. Delivery still requires a reachable backend. A reported latched stop requires a healthy backend reset; this interface does not bypass local safety.

The optional Remote access field holds a bearer token in page memory only, clearing it on reload. Authenticated API calls use the `Authorization: Bearer …` header. Tokens are never placed in a WebSocket URL or browser storage. Authenticated WebSockets send a first JSON message containing the token, as required by the backend. Authenticated HTTP polling remains available if the socket is unavailable. Configure the backend token through `NEURAVAC_API_TOKEN`; the local default needs no token.

Camera preview is opt-in. It requests `GET /api/camera` as an image every 2.5 seconds while open, with the same authorization header if configured. A missing or incompatible endpoint produces an explicit unavailable message. Camera frames do not provide cleaning observations or imply detector accuracy.

## Frontend checks

The Vitest suite covers missing/malformed telemetry, finite metrics, map projection with negative and rotated origins, invalid geometry, healthy/paused/active/terminal mission control gating, emergency-stop availability, hardware mutation prevention, empty/stale dashboard states, deterministic cloud labels, and received before/after evidence. Strict TypeScript, ESLint with zero warnings, and Vite's static build provide additional checks. Runtime backend, genuine cloud access, physical sensors, serial stop delivery, and browser-to-hardware integration still require deployment validation.
