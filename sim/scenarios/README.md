# Scenario catalog

`tests/scenarios/test_closed_loop.py` is the executable definition-of-done showcase. `test_cloud_fallback.py` adds timeout, malformed/unsafe decision and pending-cloud safety scenarios. Both use an injected deterministic simulator clock. `sim/environments/showcase.yaml` documents room coordinates in metres and seeded observation settings; scenario loading is validated by the core environment loader. Add rooms with the same schema, then supply them to SimulationRuntime.
