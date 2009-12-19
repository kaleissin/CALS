from django.test import TestCase
from django.test.client import Client

from cals.models import *

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

# __test__ = {"doctest": """
# Another way to test that 1 + 1 is equal to 2.
# 
# >>> 1 + 1 == 2
# True
# """}
# 
