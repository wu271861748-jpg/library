"""Publish searchable metadata; original fixtures are downloaded individually on use."""
import argparse, collections, gzip, hashlib, json, os, pathlib, re, subprocess, urllib.parse
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

def build(source,output,version,previous=None,validate_only=False,revision=None):
    if not re.fullmatch(r'updates-[A-Za-z0-9][A-Za-z0-9._-]{0,63}',version):
        raise ValueError('Invalid update version')
    groups = collections.defaultdict(lambda:dict(fixtures=[],paths=set()))
    for file in sorted(source.rglob('*')):
        if file.is_file() and file.suffix.lower() in ('.xml','.xmlp'):
            brand,records,target,raw = parse_fixture(file,source)
            groups[brand]['fixtures'].extend(records)
            groups[brand]['paths'].add(target)
        elif file.is_file() and file.name!='.gitkeep':
            raise ValueError(f'Only XML/XMLP belong in fixtures/: {file.relative_to(source)}')
    if validate_only:
        return dict(files=sum(len(g['paths']) for g in groups.values()),manufacturers=len(groups))
    if not revision or not re.fullmatch(r'[a-f0-9]{40}',revision):
        raise ValueError('A full Git commit is required for immutable fixture URLs')
    output.mkdir(parents=True,exist_ok=True)
    prior=previous or dict(schema=3,kind='fixture-updates',repository=REPOSITORY,version='updates-0',manufacturers=[])
    if prior.get('schema') not in (2,3) or prior.get('kind')!='fixture-updates' or prior.get('repository')!=REPOSITORY:
        raise ValueError('Not an incremental fixture index')
    old={f['path']:f for brand in prior['manufacturers'] for f in brand.get('fixtures',[])}
    manufacturers,changed_files=[],0
    for identity,group in sorted(groups.items()):
        fixtures=group['fixtures']
        for fixture in fixtures:
            previous_file=old.get(fixture['path'])
            if previous_file and (previous_file['sha256'],previous_file['bytes'])==(fixture['sha256'],fixture['bytes']):
                fixture['downloadUrl']=previous_file['downloadUrl']
                fixture['sourceUrl']=previous_file['sourceUrl']
            else:
                relative=fixture['path'].split('/ma2/online-updates/',1)[1]
                quoted=urllib.parse.quote(relative,safe='/')
                fixture['downloadUrl']=f'https://raw.githubusercontent.com/{REPOSITORY}/{revision}/fixtures/{quoted}'
                fixture['sourceUrl']=f'https://github.com/{REPOSITORY}/blob/{revision}/fixtures/{quoted}'
                changed_files+=1
        manufacturers.append(dict(id=identity,names=sorted({f['manufacturer'] for f in fixtures}),files=len(group['paths']),
                                  collections=['online-updates'],manifest=f'manufacturers/{identity}/manifest.json',fixtures=fixtures))
    changed=prior['schema']!=3 or manufacturers!=prior['manufacturers']
    index=dict(schema=3,kind='fixture-updates',repository=REPOSITORY,version=version if changed else prior['version'],manufacturers=manufacturers)
    (output/'catalog.json').write_bytes(encoded(index))
    (output/'upload-files.txt').write_text('catalog.json\n',encoding='utf8')
    return dict(publish=changed,changedFiles=changed_files,files=sum(b['files'] for b in manufacturers),index=index)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',default='updates-validation')
    parser.add_argument('--validate',action='store_true')
    parser.add_argument('--revision',help='Commit containing the fixture files (defaults to HEAD)')
    args=parser.parse_args()
    root=pathlib.Path(__file__).resolve().parents[1]
    previous=root/'updates/catalog.json'
    revision=None if args.validate else args.revision or subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    result=build(root/'fixtures',root/'release-assets',args.version,json.loads(previous.read_text(encoding='utf8')) if previous.exists() else None,args.validate,revision)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf8') as destination:
            destination.write(f"publish={str(result['publish']).lower()}\n")
    print(json.dumps({k:v for k,v in result.items() if k!='index'},ensure_ascii=True))
