"""Check that the new option serves its published files and stays distinct from Rev12."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app import app, MAIN_RETURN_DELIVERY


class MainDuctReturnTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_downloads_serve_the_published_method_package(self):
        files = [('pdf', 'Main duct and return.pdf'),
                 ('mono', 'Main duct and return - Monochrome.pdf'),
                 ('review', 'Main duct and return - Method review.pdf'),
                 ('dxf', 'Main duct and return.dxf'),
                 ('xlsx', 'Main duct and return - Registers.xlsx'),
                 ('zip', 'Main duct and return.zip')]
        for kind, name in files:
            with self.subTest(kind=kind):
                response = self.client.get('/api/main-duct-return/export/' + kind)
                try:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data, (MAIN_RETURN_DELIVERY / name).read_bytes())
                    self.assertIn(name, response.headers['Content-Disposition'])
                finally:
                    response.close()
        response = self.client.get('/api/main-duct-return/overview')
        try:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/png')
            self.assertTrue(response.data.startswith(b'\x89PNG'))
        finally:
            response.close()
        self.assertIn(b'Main duct and return', self.client.get('/').data)

    def test_missing_or_unsupported_download_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp, patch('app.MAIN_RETURN_DELIVERY', Path(temp)):
            self.assertEqual(self.client.get('/api/main-duct-return/export/pdf').status_code, 503)
            self.assertEqual(self.client.get('/api/main-duct-return/overview').status_code, 503)
        self.assertEqual(self.client.get('/api/main-duct-return/export/unknown').status_code, 400)
        self.assertEqual(self.client.get('/api/main-duct-return/export/dwg').status_code, 400)


if __name__ == '__main__':
    unittest.main()
