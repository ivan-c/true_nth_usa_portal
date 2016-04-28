"""Unit test module for Assessment Engine API"""
import json
from flask_swagger import swagger
from tests import TestCase, TEST_USER_ID


class TestAssessmentEngine(TestCase):

    def test_assessment_PUT(self):
        swagger_spec = swagger(self.app.application)
        data = swagger_spec['definitions']['QuestionnaireResponse']['example']

        self.login()
        rv = self.app.put('/api/patient/{}/assessment'.format(TEST_USER_ID),
                         content_type='application/json',
                         data=json.dumps(data))
        self.assert200(rv)
        response = rv.json
        self.assertEquals(response['ok'], True)
        self.assertEquals(response['valid'], True)

    def test_assessment_PUT_bad_date(self):
        swagger_spec = swagger(self.app.application)
        data = swagger_spec['definitions']['QuestionnaireResponse']['example']
        data['authored'] = '2016-03-11T23:4a7:2q8'

        self.login()
        rv = self.app.put('/api/patient/{}/assessment'.format(TEST_USER_ID), content_type='application/json', data=json.dumps(data))
        result = self.app.get('/api/patient/{}/assessment/epic26'.format(TEST_USER_ID), content_type='application/json', data=json.dumps(data))
        # import pdb; pdb.set_trace()

        self.assert200(rv)
        response = rv.json
        self.assertEquals(response['ok'], True)
        self.assertEquals(response['valid'], True)

    # def test_request_validation:
        # swagger_spec = swagger(self.app.application)
        # data = swagger_spec['definitions']['QuestionnaireResponse']['example']

        # self.login()
        # rv = self.app.put('/api/patient/{}/assessment'.format(TEST_USER_ID),
                         # content_type='application/json',
                         # data=json.dumps(data))
        # self.assert200(rv)
        # response = rv.json
        # self.assertEquals(response['ok'], True)
        # self.assertEquals(response['valid'], True)
