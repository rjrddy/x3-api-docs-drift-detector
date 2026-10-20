1. Diff documentation against a live OpenAPI spec and real traffic, open a PR to fix drift.

2. Result:
   Acceptance: not measured  
   Performance: not measured  
   Correctness: not measured

3. Architecture:
```mermaid
flowchart LR
    Specification --> AwaitingWaveApproval --> Implementation
```

4. Run it:
No runnable implementation yet. This is a planned Wave 3 project.

5. Decisions and limits: Public repository reserved for independent work using public or synthetic data. Implementation has not started. No company affiliation or usage is claimed. Acceptance check: Detects 10 seeded drifts; GitHub Action.

6. Next: Implement after approval for Wave 3, then run and publish the required acceptance commands.
