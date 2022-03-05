from django.test import TestCase


class BaseTestCase(TestCase):

    def get_message(self, resp):
        try:
            return resp.json()
        except:
            return resp.status_code

    def assert_status(self, resp, status_code):
        self.assertEqual(resp.status_code, status_code, self.get_message(resp))

    def assert_status_200(self, resp):
        self.assert_status(resp, 200)

    def assert_status_201(self, resp):
        self.assert_status(resp, 201)

    def assert_status_204(self, resp):
        self.assert_status(resp, 204)

    def assert_status_400(self, resp):
        self.assert_status(resp, 400)

    def assert_status_401(self, resp):
        self.assert_status(resp, 401)

    def assert_status_403(self, resp):
        self.assert_status(resp, 403)

    def assert_status_404(self, resp):
        self.assert_status(resp, 404)

    def assert_status_409(self, resp):
        self.assert_status(resp, 409)

    def assert_list_length(self, resp, length):
        if type(resp.json()) is list:
            self.assertEqual(len(resp.json()), length)
        else:
            self.assertEqual(len(resp.json()['value']), length)

    def assert_partial_dict_equal(self, dict1, dict2, keys):
        dict11 = {}
        dict22 = {}
        for key in keys:
            dict11[key] = dict1[key]
            dict22[key] = dict2[key]
        self.assertDictEqual(dict11, dict22)

    def assert_partial_dict_equal2(self, dict1, dict2, keys):
        dict11 = {}
        dict22 = {}
        for key in keys:
            dict11[key] = dict1.get(key, '')
            dict22[key] = dict2.get(key, '')
        self.assertDictEqual(dict11, dict22)

    def bill_gates(self):
        return {
            'username': 'BillGates',
            'email': 'BillGates@example.com',
            'password': 'BillGates@password'
        }
