"""Create missing Builder labels using an authenticated gh CLI; never overwrite labels."""
import json
from pathlib import Path
import subprocess

REPO = 'Schrodinger39/CMUcraft'


def main():
    labels = json.loads((Path(__file__).resolve().parents[1]/'.github/builder-labels.json').read_text())
    existing = json.loads(subprocess.check_output(
        ['gh', 'label', 'list', '--repo', REPO, '--limit', '1000', '--json', 'name'], text=True))
    names = {row['name'] for row in existing}
    for label in labels:
        if label['name'] not in names:
            subprocess.run(['gh', 'label', 'create', label['name'], '--repo', REPO,
                            '--color', label['color'], '--description', label['description']], check=True)


if __name__ == '__main__':
    main()
