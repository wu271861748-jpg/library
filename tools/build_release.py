"""Build only the future updates explicitly placed in this repository's fixtures/."""
import argparse, collections, gzip, hashlib, io, json, os, pathlib, re, urllib.parse, zipfile
import xml.etree.ElementTree as ET

REPOSITORY = 'wu271861748-jpg/library'
ALIASES = {'clay paky':'claypaky', 'robe lighting':'robe', 'robe lighting s.r.o.':'robe',
           'martin professional':'martin', 'fineart':'fine-art', 'fine art':'fine-art',
           'chauvet professional':'chauvet', 'german light products':'glp'}

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf8')

def parse_fixture(file, source):
    relative = file.relative_to(source).as_posix()
    if file.is_symlink() or not file.resolve().is_relative_to(source.resolve()):
        raise ValueError(f'Fixture must be inside fixtures/: {relative}')
    if any(part in ('.','..') or re.search(r'[<>:"\\|?*]', part) for part in relative.split('/')):
        raise ValueError(f'Unsupported fixture filename: {relative}')
    raw = file.read_bytes()
    xml = gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw
    start = xml.find(b'<?xml')
    if start >= 0:
        xml = xml[start:]
    root = ET.fromstring(xml)
    local = lambda tag: tag.rsplit('}',1)[-1]
    children = [child for child in root if local(child.tag) == 'FixtureType']
    if local(root.tag) != 'MA' or not children or any(local(c.tag) not in ('Info','FixtureType') for c in root):
        raise ValueError(f'Not a fixture-only MA2 XML/XMLP: {relative}')
    namespace = root.tag[:-2] if root.tag.startswith('{') else ''
    manufacturer = children[0].findtext(namespace+'manufacturer','').strip()
    if not manufacturer or any(c.findtext(namespace+'manufacturer','').strip()!=manufacturer for c in children):
        raise ValueError(f'Missing or mixed manufacturer: {relative}')
    brand = ALIASES.get(manufacturer.lower(),re.sub(r'[^a-z0-9]+','-',manufacturer.lower()).strip('-'))
    if not brand:
        raise ValueError(f'Manufacturer needs a usable ID: {relative}')
    target = f'manufacturers/{brand}/ma2/online-updates/{relative}'
    records = []
    for fixture in children:
        name = fixture.get('name')
        if not name:
            raise ValueError(f'Missing fixture name: {relative}')
        records.append(dict(manufacturer=manufacturer,brand=brand,name=name,mode=fixture.get('mode'),
                            xmlVersion='.'.join(root.get(k,'?') for k in ('major_vers','minor_vers','stream_vers')),
                            path=target,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),
                            collection='online-updates',sourceUrl=f'https://github.com/{REPOSITORY}/blob/main/fixtures/{urllib.parse.quote(relative)}',
                            format='MA2 XMLP' if file.suffix.lower()=='.xmlp' else 'MA2 XML'))
    return brand,records,target,raw

def build(source,output,version,previous=None,validate_only=False):
    if not re.fullmatch(r'updates-[A-Za-z0-9][A-Za-z0-9._-]{0,63}',version):
        raise ValueError('Invalid update version')
    groups = collections.defaultdict(lambda:dict(fixtures=[],payload={}))
    for file in sorted(source.rglob('*')):
        if file.is_file() and file.suffix.lower() in ('.xml','.xmlp'):
            brand,records,target,raw = parse_fixture(file,source)
            groups[brand]['fixtures'].extend(records)
            groups[brand]['payload'][target]=raw
        elif file.is_file() and file.name!='.gitkeep':
            raise ValueError(f'Only XML/XMLP belong in fixtures/: {file.relative_to(source)}')
    if validate_only:
        return dict(files=sum(len(g['payload']) for g in groups.values()),manufacturers=len(groups))
    output.mkdir(parents=True,exist_ok=True)
    prior=previous or dict(schema=2,kind='fixture-updates',repository=REPOSITORY,version='updates-0',manufacturers=[])
    if prior.get('schema')!=2 or prior.get('kind')!='fixture-updates' or prior.get('repository')!=REPOSITORY:
        raise ValueError('Not an incremental fixture index')
    old={brand['id']:brand for brand in prior['manufacturers']}
    manufacturers,uploads=[],[]
    for identity,group in sorted(groups.items()):
        manifest_path=f'manufacturers/{identity}/manifest.json'
        fixtures=group['fixtures']
        manifest=encoded(dict(id=identity,fixtures=fixtures))
        group['payload'][manifest_path]=manifest
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for name,data in sorted(group['payload'].items()):
                entry=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0))
                entry.compress_type=zipfile.ZIP_DEFLATED
                entry.external_attr=0o100644<<16
                archive.writestr(entry,data,compresslevel=9)
        packed=stream.getvalue()
        digest=hashlib.sha256(packed).hexdigest()
        filename=f'{identity}.zip'
        package=dict(url=f'https://github.com/{REPOSITORY}/releases/download/{version}/{filename}',sha256=digest,bytes=len(packed))
        if identity in old and old[identity]['package']['sha256']==digest:
            package=old[identity]['package']
        else:
            (output/filename).write_bytes(packed)
            uploads.append(filename)
        manufacturers.append(dict(id=identity,names=sorted({f['manufacturer'] for f in fixtures}),files=len(group['payload'])-1,
                                  collections=['online-updates'],manifest=manifest_path,
                                  manifestSha256=hashlib.sha256(manifest).hexdigest(),package=package))
    changed=manufacturers!=prior['manufacturers']
    index=dict(schema=2,kind='fixture-updates',repository=REPOSITORY,version=version if changed else prior['version'],manufacturers=manufacturers)
    (output/'catalog.json').write_bytes(encoded(index))
    (output/'upload-files.txt').write_text('\n'.join(uploads+['catalog.json'])+'\n',encoding='utf8')
    return dict(publish=changed,changedPackages=len(uploads),files=sum(b['files'] for b in manufacturers),index=index)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default='updates-validation')
    parser.add_argument('--validate',action='store_true')
    args=parser.parse_args()
    root=pathlib.Path(__file__).resolve().parents[1]
    previous=root/'updates/catalog.json'
    result=build(root/'fixtures',root/'release-assets',args.version,json.loads(previous.read_text(encoding='utf8')) if previous.exists() else None,args.validate)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf8') as destination:
            destination.write(f"publish={str(result['publish']).lower()}\n")
    print(json.dumps({k:v for k,v in result.items() if k!='index'},ensure_ascii=True))
