import shutil
from django.test import TestCase, override_settings


@override_settings(MEDIA_ROOT='var/media/test')
class BaseTestCase(TestCase):

    def setUp(self):
        shutil.rmtree('var/media/test', ignore_errors=True)

    def get_message(self, resp):
        try:
            data = resp.request
            data.update({'response': resp.json()})
            return data
        except:
            return resp.request

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

    def get_resp_list(self, r):
        return r.json()

    def google_org(self, visibility='Public'):
        return {
            "path": "google",
            "name": "Google LLC",
            "visibility": visibility,
            "description": "Google LLC is an American multinational technology company that specializes in Internet-related services and products, which include online advertising technologies, a search engine, cloud computing, software, and hardware." 
        }

    def microsoft_org(self, visibility='Public'):
        return {
            "path": "microsoft",
            "name": "Microsoft Corporation",
            "visibility": visibility,
            "description": "Microsoft Corporation is an American multinational technology corporation which produces computer software, consumer electronics, personal computers, and related services."
        }

    def generate_org(self, index, visibility='Public'):
        return {
            "path": "generated_org_" + format(index, '05'),
            "name": "Generated Organization " + str(index),
            "visibility": visibility,
        }

    def chrome_app(self, visibility='Public'):
        return {
            "path": "chrome",
            "name": "Google Chrome",
            "install_slug": "chrome",
            "visibility": visibility,
            "enable_os": ["iOS", "Android", "macOS"],
            "description": "Download the fast, secure browser recommended by Google."
        }

    def todo_app(self, visibility='Public'):
        return {
            "path": "todo",
            "name": "Microsoft To Do",
            "install_slug": "todo",
            "visibility": visibility,
            "enable_os": ["iOS", "Android", "macOS"],
            "description": "Create to do lists, reminders, and notes for any purpose."
        }

    def generate_app(sekf, index, visibility= 'Public'):
        return {
            "path": "generated_app_" + str(index),
            "name": "Generated UniversalApp " + str(index),
            "install_slug": "uapp"+ str(index),
            "visibility": visibility,
            "enable_os": ["iOS", "Android", "macOS"]
        }
