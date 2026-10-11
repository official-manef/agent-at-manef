"""Offline documentation links, basic source hygiene and example-contract checks."""
import ast
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
links = 0
for path in ROOT.rglob('*'):
    rel = path.relative_to(ROOT)
    if any(p in {'.git', '__pycache__', '.venv', 'build', 'dist'} or p.endswith('.egg-info') for p in rel.parts) or not path.is_file():
        continue
    if path.suffix in {'.py', '.md', '.json', '.yml', '.toml'}:
        text = path.read_text(encoding='utf-8')
        if any(line != line.rstrip() for line in text.splitlines()):
            errors.append(f'{rel}: trailing whitespace')
        if not text.endswith('\n'):
            errors.append(f'{rel}: missing final newline')
    if path.suffix == '.md':
        for href in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if href.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            dest = href.split('#', 1)[0]
            links += 1
            if not (path.parent / dest).resolve().exists():
                errors.append(f'{rel}: unresolved link {dest}')
    if path.suffix == '.py':
        tree = ast.parse(text, feature_version=(3, 10))
        used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module == '__future__':
                    continue
                for alias in node.names:
                    if (alias.asname or alias.name.split('.')[0]) not in used:
                        errors.append(f'{rel}:{node.lineno}: unused import {alias.name}')
    if path.suffix == '.json':
        json.loads(path.read_text(encoding='utf-8'))
print(json.dumps({'ok': not errors, 'relative_links_checked': links, 'errors': errors}, indent=2))
sys.exit(1 if errors else 0)
