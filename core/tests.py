from django.test import TestCase

# Create your tests here.

from rest_framework.test import APITestCase
from django.urls import reverse

class AuthTest(APITestCase):
    def test_user_registration(self):
        response = self.client.post('/api/register/', {
            "username": "test",
            "password": "pass1234"
        })
        self.assertEqual(response.status_code, 201)