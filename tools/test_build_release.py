import gzip, hashlib, pathlib, tempfile, unittest
import build_release as builder

XML=b'<?xml version="1.0"?><MA xmlns="http://schemas.malighting.de/grandma2/xml/MA" major_vers="3" minor_vers="9" stream_vers="60"><Info/><FixtureType name="Synthetic Test Fixture" mode="Mode 1"><manufacturer>Test Manufacturer</manufacturer></FixtureType></MA>'
REVISION='a'*40

class BuildTests(unittest.TestCase):
    def test_empty_does_not_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            (root/'fixtures').mkdir()
            result=builder.build(root/'fixtures',root/'out','updates-1',revision=REVISION)
            self.assertFalse(result['publish'])
            self.assertEqual(result['index']['version'],'updates-0')

    def test_metadata_only_immutable_files_and_unchanged_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            source=root/'fixtures'
            (source/'Test Manufacturer').mkdir(parents=True)
            original=gzip.compress(XML,mtime=0)
            file=source/'Test Manufacturer/test @1.xmlp'
            file.write_bytes(original)
            first=builder.build(source,root/'first','updates-1',revision=REVISION)
            self.assertEqual(first['index']['schema'],3)
            self.assertEqual(first['changedFiles'],1)
            record=first['index']['manufacturers'][0]['fixtures'][0]
            self.assertEqual(record['sha256'],hashlib.sha256(original).hexdigest())
            self.assertEqual(record['bytes'],len(original))
            self.assertEqual(record['downloadUrl'],f'https://raw.githubusercontent.com/{builder.REPOSITORY}/{REVISION}/fixtures/Test%20Manufacturer/test%20%401.xmlp')
            self.assertEqual(sorted(p.name for p in (root/'first').iterdir()),['catalog.json','upload-files.txt'])
            second=builder.build(source,root/'second','updates-2',first['index'],revision='b'*40)
            self.assertFalse(second['publish'])
            self.assertEqual(second['index'],first['index'])
            file.write_bytes(gzip.compress(XML.replace(b'Mode 1',b'Mode 2'),mtime=0))
            third=builder.build(source,root/'third','updates-3',first['index'],revision='c'*40)
            self.assertTrue(third['publish'])
            self.assertEqual(third['files'],1)
            self.assertEqual(third['changedFiles'],1)
            self.assertEqual(file.read_bytes()[:2],b'\x1f\x8b')
            self.assertIn('/'+'c'*40+'/',third['index']['manufacturers'][0]['fixtures'][0]['downloadUrl'])

    def test_previous_package_index_becomes_a_searchable_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            (root/'fixtures').mkdir()
            (root/'fixtures/test.xml').write_bytes(XML)
            old=dict(schema=2,kind='fixture-updates',repository=builder.REPOSITORY,version='updates-2',manufacturers=[])
            result=builder.build(root/'fixtures',root/'out','updates-3',old,revision=REVISION)
            self.assertTrue(result['publish'])
            self.assertEqual(result['index']['schema'],3)
            self.assertNotIn('package',result['index']['manufacturers'][0])

    def test_non_fixture_and_unpinned_urls_are_not_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            (root/'fixtures').mkdir()
            (root/'fixtures/plugin.xml').write_text('<MA><Plugin/></MA>')
            with self.assertRaises(ValueError):
                builder.build(root/'fixtures',root/'out','updates-1',revision=REVISION)
            (root/'fixtures/plugin.xml').write_bytes(XML)
            with self.assertRaises(ValueError):
                builder.build(root/'fixtures',root/'out','updates-1',revision='main')

if __name__=='__main__':
    unittest.main()
