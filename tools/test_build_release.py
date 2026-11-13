import gzip, pathlib, tempfile, unittest
import build_release as builder

XML=b'<?xml version="1.0"?><MA xmlns="http://schemas.malighting.de/grandma2/xml/MA" major_vers="3" minor_vers="9" stream_vers="60"><Info/><FixtureType name="Synthetic Test Fixture" mode="Mode 1"><manufacturer>Test Manufacturer</manufacturer></FixtureType></MA>'

class BuildTests(unittest.TestCase):
    def test_empty_does_not_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            (root/'fixtures').mkdir()
            result=builder.build(root/'fixtures',root/'out','updates-1')
            self.assertFalse(result['publish'])
            self.assertEqual(result['index']['version'],'updates-0')

    def test_only_changed_updates_and_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            source=root/'fixtures'
            source.mkdir()
            (source/'test.xmlp').write_bytes(gzip.compress(XML,mtime=0))
            first=builder.build(source,root/'first','updates-1')
            self.assertEqual(first['changedPackages'],1)
            second=builder.build(source,root/'second','updates-2',first['index'])
            self.assertFalse(second['publish'])
            self.assertEqual(second['changedPackages'],0)
            (source/'test.xmlp').write_bytes(gzip.compress(XML.replace(b'Mode 1',b'Mode 2'),mtime=0))
            third=builder.build(source,root/'third','updates-3',first['index'])
            self.assertTrue(third['publish'])
            self.assertEqual(third['files'],1)
            self.assertEqual(third['changedPackages'],1)

    def test_non_fixture_is_not_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory)
            (root/'fixtures').mkdir()
            (root/'fixtures/plugin.xml').write_text('<MA><Plugin/></MA>')
            with self.assertRaises(ValueError):
                builder.build(root/'fixtures',root/'out','updates-1')

if __name__=='__main__':
    unittest.main()
