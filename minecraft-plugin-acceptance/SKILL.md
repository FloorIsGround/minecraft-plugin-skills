---
name: minecraft-plugin-acceptance
description: Test plugins with roles, clients, and scaled workloads.
license: MIT
metadata:
  author: Floor and Codex
  version: "1.0.0"
  hermes:
    tags: [minecraft, plugins, permissions, multiplayer, testing]
---

# Minecraft plugin acceptance

Validate a plugin change through the roles, actions, dependencies, and player counts that matter to its behavior. Use for multiplayer features, permission-sensitive commands, integration changes, and bounded load investigations. Select the needed checks; a small change does not require every mode.

## Build evidence at the necessary level

- **Fast behavior checks:** test the actual source or relevant implementation against explicit dependency fixtures. Include denied and allowed actions, explicit negations, relevant defaults, and permission changes on the same player object.
- **Differential checks:** for a behavior-preserving change, feed reference and candidate identical cases and compare outputs, exceptions, and relevant event order. For a bug fix, use the intended invariant and retain an old-build failure witness.
- **Native acceptance:** use a disposable server with the actual plugin and permission provider when those semantics matter. Define player roles, perform actions, and assert consequences. Observe a client response or packet when a server API assertion alone cannot establish the user-visible result.
- **Scaled workloads:** establish the small scenario first, then vary useful dimensions independently: online players, stored accounts, permissions per loaded user, event rate, and duration. Joining many idle clients is a population test; report what those clients actually do.

Use existing project tests and build tooling when practical. Keep case-specific assertions in ordinary code. Shared helpers are most useful for server lifecycle, client lifecycle, role setup, result collection, and cleanup.

## Run and interpret

Identify the exact server, Java, plugin and dependency builds. Use fresh comparable environments for reference/candidate runs. Readiness should reflect the required condition, such as joined players and loaded permissions, rather than elapsed sleep alone. Bound startup, action, and shutdown waits; keep failure evidence and stop owned processes.

Record assertion results separately from observations. A field such as `optional_dependency_enabled: false` can be expected; an absent nullable error field is not automatically a failure. Distinguish target failures, fixture failures, and unsupported checks.

Measure the named operation after correctness checks. Preserve raw samples, warmup policy, and timing scope; interleave or alternate comparable variants when order can bias the result. A local method-speed improvement does not establish improved server TPS. A lab failure to reproduce an incident leaves its production cause unresolved.

## Examples

[The example guide](references/examples.md) supplies two newly authored fictional fixtures:

```sh
# Python standard library only; permission policies and synthetic actors.
python3 examples/roles.py --players 3 32 128 --output /tmp/role-model.json

# Optional: compile and exercise a test-only plugin with real protocol clients.
python3 examples/native.py --help
```

The native adapter uses supplied Paper assets, JDK 21+, Node, and a supplied `minecraft-protocol` installation. It runs a fresh loopback server and clients, checks actual network-issued commands across permission changes and event cancellation, and writes results into a new run directory. It downloads nothing. The guide explains its inputs and exact evidence boundary.

Dated results from fresh executions of these fictional examples are in [verification.json](references/verification.json).

The `minecraft-plugin-probes` skill, when available, provides a separate deterministic transaction bug, patch, and regression example. These skills do not depend on a shared framework or a particular mod loader.

## Deliverable

Leave a command that reruns the selected checks, source/patch identity, role and workload parameters, structured results, and the relevant limits. Preserve modeled, native API, client-visible, and performance evidence as distinct claims. Use disposable synthetic data for examples and stay within the current task's authorized environments.
