"""Harvests tags from Comsol application library to learn naming patterns."""

import mph
import json
import re
from pathlib import Path


def feature_path(node):
    """Returns the "feature path" of a node."""
    if node.is_group():
        return [node.name()]
    try:
        type = node.type()
        for taboo in ('|', '?', '→'):
            if taboo in type:
                print(f'Taboo character in type "{type}" of node "{node}".')
    except Exception:
        type = '?'
    return feature_path(node.parent()) + [type]


def harvest_tags(node):
    """Harvest tags from node and all its children."""
    if isinstance(node, mph.Model):
        node = node/None
    tags = []
    if not node.is_root():
        tag = node.tag()
        for taboo in ('|', '*'):
            if taboo in tag:
                print(f'Taboo character in tag "{tag}" of node "{node}".')
        tags.append( (tag, ' → '.join(feature_path(node))) )
    for child in node:
        tags += harvest_tags(child)
    return tags


# Specify folders to search (values) and to dump tags in (keys).
folders = {'Comsol': mph.discovery.backend()['root']}

# Dump tags and feature paths for each model.
client = None
dumps = Path(__file__).parent/'tags'
for (name, folder) in folders.items():
    print(f'Searching folder: {folder}')
    print(f'Storing tag dumps in subfolder "{name}".')

    for file in folder.rglob('*.mph'):

        # Skip models for which a tag dump already exists.
        dump = dumps/name/file.relative_to(folder).with_suffix('.txt')
        if dump.exists():
            continue

        # Start Comsol client if it isn't running already.
        if not client:
            print('Starting Comsol client.')
            client = mph.start(cores=1)

        # Load model, but skip if that fails.
        try:
            model = client.load(file)
        except Exception as error:
            if 'preview file' in str(error):
                print(f'  [preview] {file.stem}')
            else:
                print(f'  [error] {file.stem}')
            dump.parent.mkdir(exist_ok=True, parents=True)
            dump.write_text(str(error), encoding='UTF-8-sig')
            continue

        print(f'  {file.stem}')
        tags = harvest_tags(model)
        client.remove(model)

        tags = sorted(tags, key=lambda item: item[0].lower())
        dump.parent.mkdir(exist_ok=True, parents=True)
        with dump.open('w', encoding='UTF-8-sig') as stream:
            for (tag, path) in tags:
                stream.write(f'{tag:12} | {path}\n')


# Analyze tag pattern. Group by feature path. Count pattern occurrences.
print('Aggregating tag patterns from tag dumps.')
grouped = {}
for file in dumps.rglob('*.txt'):
    for line in file.open(encoding='UTF-8-sig'):
        try:
            (tag, path) = line.strip().split(' | ')
        except ValueError:
            break
        path = path.strip()
        tag = tag.strip()
        match = re.match(r'(\D+)(\d*)', tag)
        if match:
            prefix = match.group(1)
            number = match.group(2)
            if number:
                pattern = prefix + '*'
            else:
                pattern = prefix
        else:
            continue
        if pattern.startswith('builder_'):
            pattern = pattern[8:]
        if pattern.endswith('Def'):
            pattern = tag[:-3]
        if path not in grouped:
            grouped[path] = {pattern: 1}
        elif pattern not in grouped[path]:
            grouped[path][pattern] = 1
        else:
            grouped[path][pattern] += 1

# Sort grouped tag patterns by feature path.
grouped = dict(sorted(grouped.items(), key=lambda item: item[0].lower()))

# Extract ambiguous tag pattern.
print('Resolving ambiguous tag patterns.')
unique = {}
ambiguous = {}
for path in grouped:
    if len(grouped[path]) == 1:
        unique[path] = list(grouped[path].keys())[0]
    else:
        ambiguous[path] = grouped[path]

# Resolve ambiguities based on user choices.
resolve = {}
rfile = Path(__file__).parent/'resolve.txt'
if rfile.exists():
    for line in rfile.open(encoding='UTF-8-sig'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        (path, tag) = line.split(':')
        path = path.strip()
        tag = tag.strip()
        resolve[path] = tag
for path in resolve:
    unique[path] = resolve[path]
    if path in ambiguous:
        del ambiguous[path]

# Write ambiguous patterns to file if any remain unresolved.
afile = Path(__file__).parent/'ambiguous.txt'
if ambiguous:
    for path in ambiguous:
        ambiguous[path] = dict(sorted(ambiguous[path].items(),
                               key=lambda item: item[1], reverse=True))
    with afile.open('w', encoding='UTF-8-sig') as stream:
        for (path, tags) in ambiguous.items():
            stream.write(f'{path}\n')
            for (tag, count) in tags.items():
                stream.write(f'    {tag}: {count}\n')
    print(f'Ambiguous tag patterns remain, see file "{afile.name}".')
    if rfile.exists():
        print(f'Add lines to "{rfile.name}" to resolve these ambiguities.')
    else:
        print(f'Create file "{rfile.name}" to resolve these ambiguities.')
else:
    file.unlink()

# Write look-up table to JSON file if all ambiguities are resolved.
file = Path(__file__).parent/'tags.json'
unique = dict(sorted(unique.items(), key=lambda item: item[0].lower()))
if not ambiguous:
    if file.exists():
        print(f'Look-up table for tag patterns "{file.name}" already exists.')
        print('Remove the file if it needs updating.')
    else:
        with file.open('w', encoding='UTF-8-sig') as stream:
            json.dump(unique, stream, indent=0, ensure_ascii=False)
