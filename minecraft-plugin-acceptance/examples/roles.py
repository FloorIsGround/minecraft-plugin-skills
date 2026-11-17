"""Fictional policy parity and population model; no Minecraft server or clients."""
import argparse
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

ACTIONS = ('workshop.claim', 'workshop.inspect', 'workshop.manage')


@dataclass
class Actor:
    rules: dict[str, bool]
    operator: bool = False
    revision: int = 0
    cache: dict = field(default_factory=dict)

    def update(self, node, value):
        self.rules[node] = value
        self.revision += 1


def reference(actor, node):
    # Synthetic semantics: nearest explicit rule, then operator default.
    parts = node.split('.')
    keys = [node] + ['.'.join(parts[:i]) + '.*' for i in range(len(parts) - 1, 0, -1)] + ['*']
    return next((actor.rules[key] for key in keys if key in actor.rules), actor.operator)


def cached(actor, node):
    previous = actor.cache.get(node)
    if previous is None or previous[0] != actor.revision:
        previous = (actor.revision, reference(actor, node))
        actor.cache[node] = previous
    return previous[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--players', nargs='+', type=int, default=[3, 32, 128])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if any(n < 1 or n > 10000 for n in args.players):
        parser.error('population must be between 1 and 10000')
    assertions = 0

    def check(condition, detail):
        nonlocal assertions
        assertions += 1
        if not condition:
            raise AssertionError(detail)

    policies = [{}, {'workshop.*': True}, {'*': True, 'workshop.claim': False},
                {'workshop.*': False, 'workshop.claim': True}, {'workshop.inspect': True}]
    expected = [(False, False, False), (True, True, True), (False, True, True),
                (True, False, False), (False, True, False)]
    comparisons = 0
    for operator in (False, True):
        for index, policy in enumerate(policies):
            actor = Actor(dict(policy), operator)
            for i, node in enumerate(ACTIONS):
                value = reference(actor, node)
                if not operator:
                    check(value == expected[index][i], 'intended role policy')
                check(cached(actor, node) == value, 'initial parity')
                for allowed in (True, False, True, False):
                    actor.update(node, allowed)
                    check(reference(actor, node) is allowed, 'explicit grant/deny wins')
                    check(cached(actor, node) is allowed, 'same-actor cache invalidation')
                    comparisons += 1
    populations = []
    for count in args.players:
        actors = [Actor(dict(policies[i % len(policies)])) for i in range(count)]
        effects = [0] * count
        attempts = 0
        for stage in ('initial', 'revoked', 'granted', 'cancelled'):
            for index, actor in enumerate(actors):
                if stage in ('revoked', 'granted'):
                    actor.update('workshop.claim', stage == 'granted')
                allowed = reference(actor, 'workshop.claim')
                actual = cached(actor, 'workshop.claim') and stage != 'cancelled'
                intended = allowed and stage != 'cancelled'
                before = effects[index]
                if actual:
                    effects[index] += 1
                check(effects[index] - before == int(intended), f'{stage}: effect count')
                attempts += 1
        populations.append({'synthetic_actors': count, 'action_attempts': attempts,
                            'claims_granted': sum(effects), 'stages': 4})
    report = {'status': 'PASS', 'example': 'fictional workshop policy',
              'evidence_level': 'synthetic policy model',
              'assertions': {'count': assertions, 'all_passed': True},
              'observations': {'same_actor_permission_changes_checked': comparisons,
                               'populations': populations},
              'inputs': {'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
