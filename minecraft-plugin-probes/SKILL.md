---
name: minecraft-plugin-probes
description: Reproduce plugin bugs with small deterministic probes.
license: MIT
metadata:
  author: Floor and Codex
  version: "1.0.0"
  hermes:
    tags: [minecraft, plugins, debugging, regression]
---

# Minecraft plugin probes

Turn a reported plugin failure into a small executable witness, a narrow fix, and a replayable regression. Use this for inventory transactions, scheduled callbacks, permission changes, event cancellation, or other behavior whose outcome depends on a particular ordering.

## Choose the boundary

Start with the smallest boundary that can answer the question. Ordinary source tests, a tiny dependency fixture, a test plugin, or native clients can each be appropriate. Keep the real implementation under test; replace dependencies only where the test needs control. Label modeled lifecycle and scheduling behavior explicitly.

An offline witness establishes what the code does under the selected schedule. Native packet acceptance, persistence, another plugin's interference, and the deployed server build require their own evidence when material. Increase fidelity where an assumption could change the conclusion.

## Investigation loop

- State an observable invariant, such as consumed inputs matching granted outputs. Capture the initial state, actions, callback order, and final state.
- Reproduce the failure deterministically. Include a normal ordering as a control. Prefer advancing a controlled scheduler over sleeping or hoping to hit a race.
- Change the smallest transaction or state transition that fixes the invariant. Check adjacent cases that could invalidate the fix: repeated actions, closing, disconnecting, cancellation, and changed state as relevant.
- Run the same behavioral check against the old and patched implementations. The old build should demonstrate the defect; the patched build should satisfy the invariant. A bug witness succeeding is different from the plugin meeting its correctness requirements.
- Preserve a patch, exact run command, relevant input identities, structured observations, and the model assumptions. Include a seed only when the workload is randomized.

For optimizations, compare original and candidate outputs, exceptions, and relevant event/query order. For intentional bug fixes, test the intended invariant; matching the old defect is not the goal.

## Runnable example

[The fictional token-exchange example](references/example.md) includes an intentionally faulty Java implementation, an actual unified patch, and a Python runner that applies the patch and executes both versions. It uses Python 3.10+, JDK 21, and `patch`, with no Minecraft download or third-party package.

```sh
python3 examples/run.py --output /tmp/token-probe-result.json
```

Run from this skill directory, or use the script's absolute path. The runner uses a temporary build directory. The JSON report marks the original invariant violations as expected reproduction evidence and separately checks the patched behavior.

Dated results from fresh executions of this fictional example are in [verification.json](references/verification.json).

For a question involving native permissions, connected players, or workload size, use the complementary `minecraft-plugin-acceptance` skill when available. Neither skill requires the other.

## Reporting

Lead with the demonstrated mechanism and the proposed change. Keep observed values separate from assertions and report fixture failures separately from target failures. State which server behavior was modeled and which was exercised. Use only the code and environments authorized for the current task; this workflow does not authorize production experiments.
