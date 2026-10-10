"""Verify template token counts, preprocessing, and unchanged full ranking."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.embed import _model
from app.extract import extract_text
from app.preprocess import preprocess
from app.rank import rank_resumes

JD = ('Backend Developer: membangun dan memelihara aplikasi backend serta REST API '
      'menggunakan Python, database SQL, pengujian perangkat lunak, dan kolaborasi tim. '
      'Pengalaman pengembangan software dan pemecahan masalah sistem menjadi nilai tambah.')
EXPECTED = [0.3597, 0.2768, 0.2728, 0.2484, 0.2108, 0.0398]
NAMES = ['DATA01.pdf', 'DATA03.pdf', 'DATA04.pdf', 'DATA02.pdf', 'DATA06.pdf', 'DATA05.pdf']

def main():
    roles = json.loads((ROOT / 'data/roles/roles.json').read_text(encoding='utf-8'))['roles']
    print('model.max_seq_length:', _model.max_seq_length)
    for role in ('backend', 'frontend'):
        for language in ('id', 'en'):
            text = roles[role]['templates'][language]
            tokens = len(_model.tokenizer.encode(text, add_special_tokens=True, truncation=False))
            print(f'{role}/{language}: {tokens} tokens; exceeds_128={tokens > 128}')
    print('preprocess:', repr(preprocess('C++ C# .NET Node.js ui/ux ci/cd')))
    paths = sorted((ROOT / 'data/sample_cvs').glob('*.pdf'))
    assert len(paths) == 7, f'expected 7 PDFs, got {len(paths)}'
    ranking, skipped = rank_resumes(JD, {p.name: extract_text(str(p)) for p in paths})
    for name, score in ranking:
        print(f'{name}: {score:.4f}')
    print('skipped:', ', '.join(name for name, _ in skipped) or 'none')
    print('regression_match:', [name for name, _ in ranking] == NAMES and [round(score, 4) for _, score in ranking] == EXPECTED)

if __name__ == '__main__':
    main()
