from __future__ import absolute_import
from __future__ import unicode_literals

from django.test import TestCase
from django.test.client import Client

from . import models, views, admin, urls
from six.moves import range

test_user = {
            'username': 'foo',
            'password': 'bar',
        }
signup_data = {
            'username': test_user['username'],
            'password1': test_user['password'],
            'password2': test_user['password'],
        }

class SignUpTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_get_signup_page(self):
        response = self.client.get('/signup/')
        self.failUnlessEqual(response.status_code, 200)

    def test_signup(self):
        expected_url = '/signup/done/'
        response = self.client.post('/signup/', data=signup_data)
        self.assertRedirects(response, expected_url, target_status_code=404)
        response = self.client.get('/signup/')
        self.assertContains(response, 'foo')

class LoginTest(TestCase):
    fixtures = ['test.json',]

    def setUp(self):
        self.client = Client()
        response = self.client.post('/signup/', data=signup_data)

    def test_login(self):
        response = self.client.post('/', data=test_user)

# class FlatPageTest(TestCase):
#     def test_about_page(self):
#         response = self.client.get('/about/')
#         self.failUnlessEqual(response.status_code, 200)
# 
#     def test_changes_page(self):
#         response = self.client.get('/changes/')
#         self.failUnlessEqual(response.status_code, 200)
# 
#     def test_copyright_page(self):
#         response = self.client.get('/copyright/')
#         self.failUnlessEqual(response.status_code, 200)
# 
#     def test_privacy_page(self):
#         response = self.client.get('/privacy/')
#         self.failUnlessEqual(response.status_code, 200)
# 
#     def test_terms_page(self):
#         response = self.client.get('/terms/')
#         self.failUnlessEqual(response.status_code, 200)

class PageTest(TestCase):
    #fixtures = ['fixed.json', 'test_cals.json']

    def test_index(self):
        response = self.client.get('/')
        self.failUnlessEqual(response.status_code, 200)

class LanguagePageTest(TestCase):

    def test_language(self):
        response = self.client.get('/language/')
        self.failUnlessEqual(response.status_code, 301)

    def test_language_paged(self):
        response = self.client.get('/language/p1/')
        self.failUnlessEqual(response.status_code, 200)

class FeaturePageTest(TestCase):
    
    def test_feature(self):
        response = self.client.get('/feature/')
        self.failUnlessEqual(response.status_code, 301)

    def test_feature_paged(self):
        response = self.client.get('/feature/p1/')
        self.failUnlessEqual(response.status_code, 200)

    def test_feature_details_page(self):
        for feature in range(1, 142):
            response = self.client.get('/feature/%i/' % feature)
            self.failUnlessEqual(response.status_code, 200, 'Failure in feature #%i' % feature)

# __test__ = {"doctest": """
# Another way to test that 1 + 1 is equal to 2.
# 
# >>> 1 + 1 == 2
# True
# """}
# 
