1. Diff documentation against a live OpenAPI spec and real traffic, open a PR to fix drift.

2. Result:
   Seeded documentation drifts detected: 10  
   False positives on clean contracts: 0  
   Actual local HTTP responses observed: 10  

   Measured with `make bench`: [raw results](evidence/bench.json), [command output](evidence/checks.log), [environment](evidence/environment.json).

3. Architecture:
```mermaid
flowchart LR
    RunningFastAPI --> LiveOpenAPIAndHTTPTraffic --> DocumentationDiff --> ProposedRepairPR
```

4. Run it:
```sh
make setup
make lint test bench
make demo
```

5. Decisions and limits: Original local FastAPI application and actual HTTP client requests through TestClient, not traffic from a third-party service. Ten independently seeded documentation discrepancies cover paths, methods, operation IDs, parameter schema, response fields, status, requiredness and example types. Evidence retains served OpenAPI, observed traffic, drifted docs and a clean proposed repair. This checks the supported JSON/OpenAPI subset, not arbitrary prose or all OpenAPI features. The repair PR and GitHub Action are demonstrated in this own repository; no external maintainers are contacted.

6. Next: Parse markdown examples, ingest proxy traffic with redaction, and handle composed/nullable schemas.
