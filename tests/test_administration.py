import unittest
from unittest.mock import patch
from app import app, ADMIN_OUTPUT

class AdministrationTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()

    def test_project_report(self):
        response=self.client.get('/api/administration')
        self.assertEqual(response.status_code,200)
        data=response.json
        self.assertEqual(data['sections'],122)
        self.assertEqual(data['terminals'],53)
        self.assertTrue(data['ready'], 'Run scripts/build_administration.py before project validation')
        self.assertEqual(data['report']['sheets'],21)
        self.assertEqual(data['revision'],10)
        self.assertEqual(data['report']['instrumentation_coverage']['scheduled'],85)
        self.assertEqual(data['report']['instrumentation_coverage']['missing_tags'],[])
        self.assertEqual(data['report']['duct_geometry']['main_transitions'],13)
        self.assertEqual(data['report']['common_probe_attachment_checks']['count'],5)
        self.assertEqual(data['report']['duct_geometry']['unintended_same_service_intersections'],[])
        self.assertEqual(data['report']['duct_geometry']['duplicated_centerlines'],'none')
        self.assertEqual(data['report']['coordination_basis']['structural_underside_mm_affl'],4000)
        self.assertIsNone(data['report']['coordination_basis']['installed_duct_bod_mm_affl'])

    def test_downloads_match_generated_outputs(self):
        for kind,name in [('pdf','Administration_Detailed_HVAC_Duct_Flow_Diagram.pdf'),
                          ('mono','Administration_Detailed_HVAC_Duct_Flow_Diagram_Monochrome.pdf'),
                          ('zip','Administration_HVAC_Rev10.zip'),
                          ('dxf','Administration_HVAC_Detailed_Layout.dxf'),
                          ('xlsx','Administration_HVAC_Drawing_Registers_Rev10.xlsx')]:
            with self.subTest(kind=kind):
                response=self.client.get('/api/administration/export/'+kind)
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.data,(ADMIN_OUTPUT/name).read_bytes())
                response.close()
        response=self.client.get('/api/administration/overview')
        self.assertEqual(response.status_code,200)
        response.close()

    def test_dwg_without_engine(self):
        with patch('app.converter', return_value=None):
            self.assertEqual(self.client.get('/api/administration/export/dwg').status_code,503)
        self.assertEqual(self.client.get('/api/administration/export/unknown').status_code,400)

if __name__=='__main__':
    unittest.main()
