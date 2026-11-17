# Fictional example: token exchange

This is newly authored teaching code. It is not a transcript, a customer incident, a real plugin implementation, or historical execution evidence.

A crafting station exchanges two carried tokens for one badge. Its faulty handler grants the badge immediately and schedules a later cursor debit. Closing the screen can return the old cursor to storage before that debit; two clicks can also spend the same unconsumed input. The model exposes both orderings directly.

Run from the skill directory:

```sh
python3 examples/run.py --output /tmp/token-probe-result.json
```

The runner compiles and executes the original, applies `examples/atomic-debit.patch` to a temporary copy, and compiles and executes that copy. It expects the original to violate conservation for selected schedules and the patched copy to preserve it for every case. Missing tools, compilation failures, malformed output, or an unexpected original result fail the overall runner.

The invariant is:

```text
stored tokens + carried tokens + 2 × badges = initial tokens
```

`TokenExchange.java` models cursor return, connection status, and a scheduler. These are plain Java fixtures, not Minecraft inventory code or native packet scheduling. The toy operation has no external output API that can throw; a real fix must address failure/rollback if its commit can fail. Do not transplant the patch into another plugin without checking its transaction semantics.

To adapt the method, keep a real call into the code being investigated, identify the smallest necessary dependency fixtures, and define expected state independently of implementation details. For a native follow-up, drive the same user action on the target server and verify the persisted inventory or other externally meaningful result.

Useful handoff contents are the reproduction command, failing schedule, old and fixed observations, exact patch, input/build identities, and remaining native assumptions. The example report contains source/patch hashes and separate assertion and observation fields. Generated reports belong with the investigation, not in the installed skill.
