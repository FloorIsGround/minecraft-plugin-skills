# Fictional workshop examples

All example code is newly authored for teaching. It does not describe a real incident, customer plugin, historical workload, or historical result.

## Fast policy and scale model

From the skill directory:

```sh
python3 examples/roles.py --players 3 32 128 --output /tmp/role-model.json
```

The example compares a straightforward permission resolver with a cached resolver whose entries include the policy revision. It exercises exact grants and denials, wildcard rules, operator defaults, default denial, and grant/revoke cycles on the same actor. Its synthetic permission semantics are defined in the code; it does not implement Bukkit or LuckPerms.

Each population performs claim attempts before and after role changes and event cancellation. The result reports actor counts and verified behavior, with `evidence_level: synthetic policy model`. These are synthetic actors in Python, not native Minecraft players or production load measurements. Adjust dimensions to the question; the sample sizes are examples, not required profiles.

## Native player and command example

The `native/WorkshopExample.java` plugin is a test-only feature and acceptance fixture. Players named `WorkshopNNN` receive one of four synthetic roles: guest, maker, reviewer, or restricted operator. A successful `/workshop claim` increments an in-memory counter. Test stages exercise the initial roles, revocation, grants, and cancellation of a real Bukkit event. Commands are sent by headless clients through the Minecraft protocol, not dispatched by the server as those players.

Prerequisites:

- A full JDK matching the supplied server (JDK 21 suffices for the tested Paper 1.21.8 fixture).
- Node and a supplied `minecraft-protocol` installation with the target protocol schema. The adapter was authored against 1.68.0; use a dependency lock for repeatable future runs. This skill does not bundle node_modules.
- A prepared Paper directory containing `server.jar`, `libraries/`, and `libraries.json`. The manifest is a list of `{ "path": "relative/library.jar", "sha256": "..." }` records under `libraries/`. Verify the server's published identity separately; local hashes establish repeatability, not authenticity.
- Acceptance of the Minecraft EULA for the disposable local run, supplied with `--accept-eula`.

```sh
python3 examples/native.py \
  --paper-assets /path/to/prepared-paper \
  --client-module /path/to/node_modules/minecraft-protocol \
  --version 1.21.8 --players 4 --accept-eula \
  --run-directory /tmp/workshop-native-small
```

After the small case works, repeat with a new directory and a larger `--players` value, for example 32. The runner compiles only this fictional source, creates the test plugin JAR, verifies the supplied library hashes, and launches Java and Node as owned child processes. The server binds to loopback on a selected free port, uses an offline synthetic-player setup, a fresh flat world, and a bounded heap. Stop and cleanup run even after an assertion failure. Supplied assets are read-only inputs; worlds, logs, classes, JARs, and results go into the new run directory. It does not install a service, use account credentials, or contact a production server. This loopback adapter is not a network sandbox; use the project's container runner if outbound network isolation is needed.

Results distinguish native assertions from observations. A passing native run establishes connected players, command processing under role changes, event cancellation, and the fixture's counters. It does not establish real permission-provider behavior, rendered GUI state, persistence, other plugin interactions, or production performance. Add the actual provider and those actions when they are the subject of the investigation.

The runner deliberately requires supplied assets instead of becoming a server installer. Replace its environment adapter with an existing project runner when available. Keep the role/action assertions and result boundary; ports, paths, and player counts are parameters.
