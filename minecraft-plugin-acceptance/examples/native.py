"""Build and run the fictional workshop fixture using supplied local assets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import zipfile

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value) + '\n')
    temporary.replace(path)


def stop(process, command=None):
    if process is None or process.poll() is not None:
        return
    if command:
        try:
            process.stdin.write(command + '\n')
            process.stdin.flush()
            process.wait(timeout=35)
            return
        except (BrokenPipeError, subprocess.TimeoutExpired):
            pass
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper-assets', type=Path, required=True)
    parser.add_argument('--client-module', type=Path, required=True)
    parser.add_argument('--run-directory', type=Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--players', type=int, default=4)
    parser.add_argument('--java', default='java')
    parser.add_argument('--node', default='node')
    parser.add_argument('--accept-eula', action='store_true')
    args = parser.parse_args()
    if not args.accept_eula:
        parser.error('--accept-eula is required for this disposable server')
    if not 1 <= args.players <= 512:
        parser.error('--players must be between 1 and 512 for this example')
    assets = args.paper_assets.resolve()
    module = args.client_module.resolve()
    for p in [assets / 'server.jar', assets / 'libraries.json', module / 'package.json']:
        if not p.is_file():
            parser.error(f'Missing supplied asset: {p}')
    records = json.loads((assets / 'libraries.json').read_text())
    libraries = []
    library_root = (assets / 'libraries').resolve()
    for row in records:
        path = (library_root / row['path']).resolve()
        if not path.is_relative_to(library_root) or sha(path) != row['sha256']:
            raise ValueError('Supplied library manifest mismatch')
        libraries.append(path)
    classpath = os.pathsep.join(str(p) for p in [assets / 'server.jar', *libraries])
    run = args.run_directory.resolve()
    run.mkdir(parents=True, exist_ok=False)
    classes = run / 'classes'
    classes.mkdir()
    sources = sorted((ROOT / 'native').glob('*.java'))
    compiled = subprocess.run([args.java, '--module', 'jdk.compiler/com.sun.tools.javac.Main',
                               '--source', '21', '--target', '21', '-proc:none', '-cp', classpath, '-d', str(classes),
                               *map(str, sources)], capture_output=True, text=True, timeout=40)
    (run / 'compile.log').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode:
        raise RuntimeError('Example compilation failed; see ' + str(run / 'compile.log'))
    plugins = run / 'plugins'
    plugins.mkdir()
    plugin = plugins / 'WorkshopExample.jar'
    with zipfile.ZipFile(plugin, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(ROOT / 'native/plugin.yml', 'plugin.yml')
        for p in sorted(classes.rglob('*.class')):
            archive.write(p, p.relative_to(classes).as_posix())
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    (run / 'eula.txt').write_text('eula=true\n')
    (run / 'server.properties').write_text(
        f'server-ip=127.0.0.1\nserver-port={port}\nmax-players={args.players + 2}\n'
        'online-mode=false\nenforce-secure-profile=false\nlevel-name=world\nlevel-seed=42\n'
        'level-type=minecraft:flat\ngenerate-structures=false\nview-distance=2\nsimulation-distance=2\n'
        'spawn-protection=0\nspawn-monsters=false\npause-when-empty-seconds=-1\n'
        'enable-rcon=false\nenable-query=false\n')
    (run / 'bukkit.yml').write_text('settings:\n  connection-throttle: -1\n  allow-end: false\n')
    command = [args.java, '-Xms256m', '-Xmx1024m', '-XX:ActiveProcessorCount=2',
               '-Dterminal.jline=false', '-Dterminal.ansi=false',
               f'-Dworkshop.players={args.players}', '-cp', classpath,
               'org.bukkit.craftbukkit.Main', '--nogui']
    receipt = {'example': 'fictional workshop', 'status': 'FAIL', 'players': args.players,
               'evidence_level': 'native Paper players and network-issued commands',
               'inputs': {'server_sha256': sha(assets / 'server.jar'),
                          'libraries_manifest_sha256': sha(assets / 'libraries.json'),
                          'plugin_sha256': sha(plugin), 'protocol_version': args.version,
                          'client_package_version': read(module / 'package.json').get('version'),
                          'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p)
                              for p in [Path(__file__).resolve(), *sorted((ROOT / 'native').iterdir())] if p.is_file()}},
               'observations': {'port': port, 'heap_limit_mib': 1024,
                                'external_permission_provider': False}}
    server = clients = None
    fixture = plugins / 'WorkshopExample'
    started = time.monotonic()
    server_log = (run / 'server.log').open('w')
    clients_log = (run / 'clients.log').open('w')

    def wait_for(predicate, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError('Server exited before acceptance completed')
            errors = read(run / 'clients.json')
            if errors.get('errors') or errors.get('ended'):
                raise RuntimeError('A native client failed; see clients.json')
            if clients is not None and clients.poll() is not None:
                raise RuntimeError('Native client process exited early')
            result = read(fixture / 'result.json')
            if result.get('status') == 'FAIL':
                raise AssertionError('Fixture or target check failed; see plugin result.json')
            if predicate():
                return
            if (run / 'server.log').stat().st_size > 16 * 1024 * 1024:
                raise RuntimeError('Unexpected log volume')
            time.sleep(.2)
        raise TimeoutError('Native fixture readiness/action deadline exceeded')

    def console(action):
        server.stdin.write('workshoplab ' + action + '\n')
        server.stdin.flush()

    try:
        server = subprocess.Popen(command, cwd=run, stdin=subprocess.PIPE,
                                  stdout=server_log, stderr=subprocess.STDOUT, text=True)
        wait_for(lambda: read(fixture / 'phase.json').get('stage') == 'joining', 120)
        clients = subprocess.Popen([args.node, str(ROOT / 'native/clients.js'), str(module),
                                    str(run), str(port), args.version, str(args.players)],
                                   stdout=clients_log, stderr=subprocess.STDOUT, text=True)
        wait_for(lambda: len(read(run / 'clients.json').get('ready', [])) == args.players
                 and read(fixture / 'state.json').get('online') == args.players, 90)
        console('prepare')
        for index, stage in enumerate(('initial', 'revoked', 'granted', 'cancelled')):
            wait_for(lambda: read(fixture / 'phase.json').get('stage') == stage, 10)
            atomic_json(run / 'send.json', {'stage': stage})
            wait_for(lambda: read(fixture / 'state.json').get('processed') == args.players * (index + 1), 25)
            console('verify_' + stage)
        wait_for(lambda: read(fixture / 'result.json').get('status') == 'PASS', 10)
        receipt['native'] = read(fixture / 'result.json')
        receipt['clients'] = read(run / 'clients.json')
        stages = receipt['clients'].get('stages_sent', [])
        if len(receipt['clients']['ready']) != args.players or len(stages) != 4:
            raise AssertionError('Incomplete client evidence')
        receipt['status'] = 'PASS'
    except BaseException as error:
        receipt['fixture_error'] = repr(error)
    finally:
        stop(clients)
        stop(server, 'stop')
        server_log.close()
        clients_log.close()
        receipt['observations']['server_exit_code'] = None if server is None else server.returncode
        receipt['observations']['wall_seconds'] = round(time.monotonic() - started, 2)
        receipt['assertions'] = {'behavior_checks_passed': receipt['status'] == 'PASS',
                                 'server_exit_zero': server is not None and server.returncode == 0}
        if not all(receipt['assertions'].values()):
            receipt['status'] = 'FAIL'
        atomic_json(run / 'result.json', receipt)
    print(json.dumps({'status': receipt['status'], 'players': args.players,
                      'native_assertions': len(receipt.get('native', {}).get('assertions', [])),
                      'fixture_error': receipt.get('fixture_error'),
                      'report': str(run / 'result.json')}))
    raise SystemExit(0 if receipt['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
