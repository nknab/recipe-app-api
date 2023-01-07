"""
Test for the User API
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    """
    Creates a new user
    """
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """
    API Requests that do not require Authentication
    """

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """
        Test the creation of a new User
        """
        payload = {
            'email': 'test@example.com',
            'password': 'testpassword1234',
            'name': 'Test Name'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))

        self.assertNotIn('password', res.data)

    def test_user_with_email_exist(self):
        """
        Raise an error when the email already exist
        """
        payload = {
            'email': 'test@example.com',
            'password': 'testpassword1234',
            'name': 'Test Name'
        }

        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """
        Raise an error when the password is too short.
        """
        payload = {
            'email': 'test@example.com',
            'password': 'pas',
            'name': 'Test Name'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """
        Test token generation for valid credentials
        """
        user_details = {
            'email': 'test@example.com',
            'password': 'testpassword1234',
            'name': 'Test Name'
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_for_bad_credentials(self):
        """
        Raise an error if credentials are invalid
        """
        user_details = {
            'email': 'test@example.com',
            'password': 'testpassword1234',
            'name': 'Test Name'
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': 'pass'
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_blank_password(self):
        """
        Raise an error if a blank password was provided
        """

        payload = {
            'email': 'test@example.com',
            'password': ''
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """
        Test make sure authentication is required
        """

        res = self.client.post(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """
    API Requests that do require Authentication
    """

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpassword1234',
            name='Test Name'
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """
        Retrieving details of an authenticated user
        """

        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_not_allowed(self):
        """
        Raise error for POST Method to endpoint not allowed
        """

        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """
        Test updating user details
        """

        payload = {
            'password': 'newpassword',
            'name': 'New Name'
        }

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()

        self.assertTrue(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
