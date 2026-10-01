#!/usr/bin/env python3
"""Check port documentation paths and source inventories; does not certify parity."""
from pathlib import Path
import csv
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
PORT = ROOT / 'rust-port'
errors = []


def fail(message):
    errors.append(message)


def read_tsv(name):
    with (PORT / 'docs' / name).open(newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


for doc in PORT.rglob('*.md'):
    if 'target' in doc.relative_to(PORT).parts:
        continue
    text = doc.read_text()
    for target in re.findall(r'\[[^\]\n]*\]\(([^)]+)\)', text):
        if re.match(r'^[a-zA-Z][\w+.-]*:', target) or target.startswith('#'):
            continue
        path = unquote(target.split('#', 1)[0].split(' "', 1)[0].strip('<>'))
        if path and not (doc.parent / path).exists():
            fail(f'{doc.relative_to(ROOT)}: missing link {target}')
    for number, line in enumerate(text.splitlines(), 1):
        if line.rstrip() != line:
            fail(f'{doc.relative_to(ROOT)}:{number}: trailing whitespace')

coverage = read_tsv('coverage-ledger.tsv')
expected = set()
for surface, source in [('workspace', 'src/preload/index.ts'),
                        ('pet-overlay', 'src/preload/pet-overlay.ts')]:
    body = (ROOT / source).read_text().split('const api = {', 1)[1].split('\n};', 1)[0]
    names = re.findall(r'^  (\w+):', body, re.M)
    if not names or len(names) != len(set(names)):
        fail(f'{source}: API inventory parser needs review')
    for name in names:
        expected.add((surface, 'subscription' if name.startswith('on') else 'operation', source, name))
actual = [(r['surface'], r['kind'], r['source'], r['operation']) for r in coverage]
# Independent child actions may be added with a colon suffix; every base API remains required.
base_actual = [key for key in actual if ':' not in key[3]]
if len(actual) != len(set(actual)):
    fail('coverage-ledger.tsv: duplicate row identity')
for missing in sorted(expected - set(base_actual)):
    fail(f'coverage-ledger.tsv: missing current API {missing}')
for obsolete in sorted(set(base_actual) - expected):
    fail(f'coverage-ledger.tsv: obsolete/incorrect API {obsolete}')

inventory = read_tsv('source-inventory.tsv')
expected_files = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'src/renderer').rglob('*') if p.is_file()}
expected_files.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'src/preload').glob('*.ts'))
expected_files.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'scripts').glob('verify-*.cjs'))
actual_files = [r['source'] for r in inventory]
if len(actual_files) != len(set(actual_files)):
    fail('source-inventory.tsv: duplicate source')
for missing in sorted(expected_files - set(actual_files)):
    fail(f'source-inventory.tsv: missing {missing}')
for obsolete in sorted(set(actual_files) - expected_files):
    fail(f'source-inventory.tsv: obsolete {obsolete}')

cards = (PORT / 'docs/task-cards.md').read_text()
card_ids = set(re.findall(r'^## (R\d+):', cards, re.M))
for name, rows in [('coverage-ledger.tsv', coverage), ('source-inventory.tsv', inventory)]:
    for row in rows:
        if row['status'] not in {'planned', 'implemented', 'tested', 'accepted', 'blocked', 'deferred'}:
            fail(f'{name}: unknown status for {row}')
        if row['task'] != 'unassigned' and row['task'] not in card_ids:
            fail(f'{name}: unknown task {row["task"]}')
        if row['status'] == 'accepted':
            fields = (['authoritative_owner', 'native_view_action', 'transport_disposition',
                       'identity_fence', 'success_refusal_uncertain', 'test_fixture',
                       'native_platform_evidence', 'reviewer'] if name.startswith('coverage')
                      else ['disposition', 'test_native_evidence'])
            if any(not row[field].strip() or row[field] in {'unreviewed', 'pending'} for field in fields):
                fail(f'{name}: accepted row lacks required evidence: {row}')

for crate in ['gpui-prototype', 'gpui-feasibility']:
    manifest = (PORT / crate / 'Cargo.toml').read_text()
    pin = '66432e4ca957383dcc9ec61d1353a4b4bd94c6bc'
    if pin not in manifest or not (PORT / crate / 'Cargo.lock').exists():
        fail(f'{crate}: missing reviewed pin or lockfile')

if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print(f'Documentation checks passed: {len(card_ids)} task cards, {len(expected)} API entries, '
      f'{len(expected_files)} source/reference files. Planning inventory only; no parity claim.')
