"""Execute the fictional bug witness, apply its patch, and check the invariant."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def execute(source, build):
    build.mkdir()
    compiled = subprocess.run([
        'java', '--module', 'jdk.compiler/com.sun.tools.javac.Main', '--source', '21', '--target', '21',
        '-d', str(build), str(source),
    ], capture_output=True, text=True, timeout=30)
    if compiled.returncode:
        raise RuntimeError('Example compilation failed: ' + compiled.stderr)
    run = subprocess.run(['java', '-cp', str(build), 'TokenExchange'],
                         capture_output=True, text=True, timeout=10)
    if run.returncode not in (0, 1) or run.stderr:
        raise RuntimeError(f'Unexpected JVM outcome: {run.returncode}: {run.stderr}')
    rows = [json.loads(line) for line in run.stdout.splitlines()]
    expected = {f'{name}/{count}' for count in (0, 1, 2, 7) for name in (
        'normal', 'close_before_callback', 'two_clicks_before_callback',
        'disconnect_before_callback')}
    if len(rows) != len(expected) or {row['case'] for row in rows} != expected:
        raise AssertionError('Incomplete or unexpected probe cases')
    return {'exit_code': run.returncode, 'cases': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='token-probe-') as name:
        root = Path(name)
        original = execute(ROOT / 'TokenExchange.java', root / 'original-classes')
        source = root / 'TokenExchange.java'
        source.write_bytes((ROOT / 'TokenExchange.java').read_bytes())
        subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i',
                        str(ROOT / 'atomic-debit.patch')], cwd=root,
                       check=True, capture_output=True, text=True, timeout=10)
        fixed = execute(source, root / 'fixed-classes')
    old = {row['case']: row['assertions'] for row in original['cases']}
    expected_failures = {'close_before_callback/7', 'two_clicks_before_callback/7',
                         'disconnect_before_callback/7'}
    reproduced = all(old[name]['tokens_conserved'] is False for name in expected_failures)
    controls = all(all(values.values()) for name, values in old.items()
                   if name.startswith('normal/') or name.endswith('/0') or name.endswith('/1'))
    fixed_pass = fixed['exit_code'] == 0 and all(
        all(row['assertions'].values()) for row in fixed['cases'])
    assertions = {'original_defect_reproduced': reproduced and original['exit_code'] == 1,
                  'original_controls_pass': controls, 'patched_invariants_pass': fixed_pass}
    report = {
        'example': 'fictional token exchange', 'evidence_level': 'offline lifecycle model',
        'status': 'PASS' if all(assertions.values()) else 'FAIL', 'assertions': assertions,
        'observations': {'original': original, 'patched': fixed},
        'inputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (ROOT / 'TokenExchange.java', ROOT / 'atomic-debit.patch')},
    }
    encoded = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(encoded)
    print(json.dumps({'status': report['status'], 'assertions': assertions,
                      'cases_per_build': len(fixed['cases'])}))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
