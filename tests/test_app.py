import copy
import io
import os
import unittest
from unittest.mock import patch
import ezdxf
from app import app, SAMPLE, drawing, validate, outline

class DrawingTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_sample_preview_and_velocity(self):
        response = self.client.post('/api/preview', json=SAMPLE)
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(response.json['velocities'][0], 3.75)
        self.assertEqual(len(response.json['outlines']), 2)

    def test_export_is_valid_cad_with_dimensions_and_layers(self):
        response = self.client.post('/api/export/dxf', json=SAMPLE)
        self.assertEqual(response.status_code, 200)
        doc = ezdxf.read(io.StringIO(response.data.decode('utf-8')))
        self.assertEqual(doc.units, ezdxf.units.MM)
        self.assertFalse(doc.audit().has_errors)
        self.assertEqual(len(doc.modelspace().query('DIMENSION')), 5)
        self.assertEqual(len(doc.modelspace().query('LWPOLYLINE[layer=="DUCT"]')), 2)
        texts = [e.dxf.text for e in doc.modelspace().query('TEXT')]
        self.assertTrue(any('600x400' in t and '3.75 m/s' in t for t in texts))
        self.assertIn('AHU-01', texts)
        self.assertEqual(texts.count('MITER ELBOW'), 3)

    def test_miter_outline(self):
        polygon = outline([[0, 0], [1000, 0], [1000, 1000]], 200)
        self.assertEqual(polygon, [(0, 100), (900, 100), (900, 1000), (1100, 1000), (1100, -100), (0, -100)])

    def test_invalid_models(self):
        for replacement in (0, -100, None, 'bad', True, float('inf')):
            model = copy.deepcopy(SAMPLE)
            model['routes'][0]['width'] = replacement
            with self.subTest(width=replacement):
                self.assertEqual(self.client.post('/api/preview', json=model).status_code, 400)
        for points in ([[0,0]], [[0,0],[0,0]], [[0,0],[1000,1000]], [[0,0],[1000,0],[0,0]]):
            model=copy.deepcopy(SAMPLE)
            model['routes'][0]['points']=points
            self.assertEqual(self.client.post('/api/export/dxf', json=model).status_code, 400)

    def test_dwg_missing_engine_is_explicit(self):
        with patch('app.converter', return_value=None):
            self.assertFalse(self.client.get('/api/status').json['dwg_available'])
            response=self.client.post('/api/export/dwg', json=SAMPLE)
            self.assertEqual(response.status_code, 503)
            self.assertIn('ODA', response.json['error'])

    def test_failed_converter_does_not_return_fake_dwg(self):
        with patch('app.converter', return_value='/opt/oda/ODAFileConverter'), patch('app.subprocess.run') as run:
            run.return_value.returncode=1
            self.assertEqual(self.client.post('/api/export/dwg',json=SAMPLE).status_code,502)
            self.assertEqual(run.call_args.args[0][-5:],['ACAD2018','DWG','0','1','drawing.dxf'])

    def test_home_and_json_errors(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.post('/api/preview', data='{', content_type='application/json').status_code,400)
        self.assertEqual(self.client.post('/api/preview',json=[]).status_code,400)

if __name__ == '__main__':
    unittest.main()
