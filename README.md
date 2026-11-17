# Minecraft plugin skills

Two reusable agent skills for developing and debugging Minecraft plugins through small experiments, reproducible patches, multiplayer checks, and bounded workloads.

- [minecraft-plugin-probes](minecraft-plugin-probes/SKILL.md): reproduce a timing-sensitive bug, apply a narrow patch, and replay the behavioral checks.
- [minecraft-plugin-acceptance](minecraft-plugin-acceptance/SKILL.md): check permission roles and changes, native player actions, event cancellation, and larger player populations.

The skills provide guidance and adaptable example code. Choose the smallest test that answers the question, and increase fidelity when a modeled assumption could affect the conclusion. Existing project tests and runners can supply the execution environment.

## Examples

All examples are fictional, newly authored teaching code. Verification records describe fresh executions of these examples. No Minecraft server binaries or client dependencies are bundled.

### Deterministic bug and patch

Requires Python 3.10+, a full JDK 21, and `patch`:

```sh
python3 minecraft-plugin-probes/examples/run.py --output /tmp/token-probe-result.json
```

The runner executes an intentionally faulty token exchange, applies the included unified patch to a temporary copy, and checks the same invariants against both versions. The recorded run reproduced the defect and passed all 16 cases after patching. See the [example guide](minecraft-plugin-probes/references/example.md) and [dated verification](minecraft-plugin-probes/references/verification.json).

### Permission model and population checks

Requires Python 3.10+ and its standard library:

```sh
python3 minecraft-plugin-acceptance/examples/roles.py \
  --players 3 32 128 --output /tmp/role-model.json
```

This exercises synthetic policy semantics, cached/reference behavior, permission changes on the same actor, and action effects. These populations are modeled actors, not Minecraft players.

### Native multiplayer checks

The optional native adapter compiles the fictional workshop plugin and uses connected protocol clients to issue commands through role changes and event cancellation:

```sh
python3 minecraft-plugin-acceptance/examples/native.py --help
```

It requires supplied, prepared Paper assets, a matching JDK, Node, and a `minecraft-protocol` installation. Read the [native example guide](minecraft-plugin-acceptance/references/examples.md) for the input format and invocation. Each run creates a fresh loopback server and synthetic clients in a new directory. The local runner is not a network sandbox.

Recorded runs passed with four and 32 native players and clean server shutdown. These tests use synthetic permission attachments and bounded actions; they do not establish external permission-provider behavior or production capacity. See the [dated verification](minecraft-plugin-acceptance/references/verification.json) for the exact scope and input identities.

## Install

Each top-level skill directory is self-contained. Install either skill independently or both.

### Codex

Use the installed skill installer:

```sh
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-installer/scripts/install-skill-from-github.py" \
  --repo FloorIsGround/minecraft-plugin-skills \
  --path minecraft-plugin-probes minecraft-plugin-acceptance
```

Alternatively, place the two skill directories in your personal Codex skills directory. Invoke them as `$minecraft-plugin-probes` and `$minecraft-plugin-acceptance`.

### Hermes

After cloning this repository, copy the skill directories into your personal skills library:

```sh
mkdir -p ~/.hermes/skills/gaming
cp -R minecraft-plugin-probes minecraft-plugin-acceptance ~/.hermes/skills/gaming/
```

The instructions use ordinary filesystem, process, Java, Python, and Node tools; they do not depend on a particular agent-specific execution API.

## License

[MIT](LICENSE). Supplied server and dependency artifacts retain their own licenses.
