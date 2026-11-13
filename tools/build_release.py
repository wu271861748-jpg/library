"""Build deterministic, fixture-only GitHub Release assets. No upload or credentials."""
import argparse
import hashlib
import io
import json
import pathlib
import re
import zipfile

REPOSITORY = 'wu271861748-jpg/library'
FIELDS = ('manufacturer', 'brand', 'name', 'mode', 'xmlVersion', 'path', 'bytes',
          'sha256', 'collection', 'sourceUrl', 'sourcePage', 'format',
          'manufacturerDiffersFromDownloadBrand')


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf8')


def build(source, output, version, previous=None):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}', version):
        raise ValueError('Invalid data version')
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents:
        raise ValueError('Release output must be outside the source library')
    output.mkdir(parents=True, exist_ok=True)
    manufacturers = json.loads((source / '_index/manufacturers.json').read_text(encoding='utf8'))
    old = {}
    if previous:
        prior = json.loads(previous.read_text(encoding='utf8'))
        if prior.get('schema') != 1 or prior.get('repository') != REPOSITORY:
            raise ValueError('Previous index uses a different repository/schema')
        old = {item['id']: item for item in prior['manufacturers']}
    result, uploads = [], []
    for ordinal, brand in enumerate(manufacturers):
        identity = brand['id']
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', identity):
            raise ValueError('Invalid manufacturer ID')
        manifest_path = f'manufacturers/{identity}/manifest.json'
        if brand['manifest'] != manifest_path:
            raise ValueError(f'Unexpected manifest: {identity}')
        raw_manifest = json.loads((source / manifest_path).read_text(encoding='utf8'))
        fixtures, payload = [], {}
        for raw in raw_manifest['fixtures']:
            fixture = {field: raw[field] for field in FIELDS if field in raw}
            relative = fixture['path']
            parts = pathlib.PurePosixPath(relative)
            if (fixture['brand'] != identity or '\\' in relative or parts.is_absolute()
                    or '..' in parts.parts or not relative.startswith(f'manufacturers/{identity}/ma2/')
                    or parts.suffix.lower() not in ('.xml', '.xmlp')):
                raise ValueError(f'Out-of-scope fixture: {relative}')
            data = (source / relative).read_bytes()
            if len(data) != fixture['bytes'] or hashlib.sha256(data).hexdigest() != fixture['sha256']:
                raise ValueError(f'Fixture bytes differ from manifest: {relative}')
            fixtures.append(fixture)
            payload[relative] = data
        manifest = dict(id=identity, fixtures=fixtures)
        payload[manifest_path] = json_bytes(manifest)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(payload.items()):
                item = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                item.compress_type = zipfile.ZIP_DEFLATED
                item.external_attr = 0o100644 << 16
                archive.writestr(item, data, compresslevel=9)
        packed = stream.getvalue()
        digest = hashlib.sha256(packed).hexdigest()
        filename = f'manufacturer-{ordinal:04d}.zip'
        package = dict(url=f'https://github.com/{REPOSITORY}/releases/download/library-{version}/{filename}',
                       sha256=digest, bytes=len(packed))
        prior = old.get(identity)
        if prior and prior['package']['sha256'] == digest:
            package = prior['package']
        else:
            destination = output / filename
            if destination.exists() and destination.read_bytes() != packed:
                raise ValueError(f'Existing output differs: {filename}')
            destination.write_bytes(packed)
            uploads.append(filename)
        result.append(dict(id=identity, names=brand['names'], files=len(payload)-1,
                           collections=brand['collections'], manifest=manifest_path,
                           manifestSha256=hashlib.sha256(payload[manifest_path]).hexdigest(), package=package))
    index = dict(schema=1, repository=REPOSITORY, version=version, manufacturers=result)
    (output / 'catalog.json').write_bytes(json_bytes(index))
    (output / 'upload-files.txt').write_text('\n'.join(uploads + ['catalog.json']) + '\n', encoding='utf8')
    report = dict(version=version, manufacturers=len(result), files=sum(b['files'] for b in result),
                  changedPackages=len(uploads), uploadBytes=sum((output / f).stat().st_size for f in uploads),
                  indexSha256=hashlib.sha256(json_bytes(index)).hexdigest())
    (output / 'build-summary.json').write_bytes(json_bytes(report))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--previous', type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.output, args.version, args.previous), ensure_ascii=True))
