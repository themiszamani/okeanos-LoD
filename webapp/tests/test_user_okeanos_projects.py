import mock

from rest_framework import status
from rest_framework.test import APITestCase

from backend.models import User
from backend.response_messages import ResponseMessages

class TestUserOkeanosProjects(APITestCase):
    """
    Contains tests for user okeanos projects API call.
    """

    # Define a fake ~okeanos token.
    AUTHENTICATION_TOKEN = "fake-token"

    def setUp(self):
        # Create a user and force authenticate.
        self.user = User.objects.create(uuid=uuid.uuid4())
        self.client.force_authenticate(user=self.user)

        # Add a fake token to every request authentication header to be used by the API.
        self.client.credentials(HTTP_AUTHORIZATION='Token {token}'.format(token=self.
                                                                          AUTHENTICATION_TOKEN))

    # Test for getting the user ~okeanos projects.
    @mock.patch('backend.views.get_user_okeanos_projects', return_value=[
        {'id': 1, 'name': "name1"},
        {'id': 2, 'name': "name2"}])
    def test_user_okeanos_projects(self):

        # Make a request to get the user okeanos projects.
        response = self.client.get("/api/user-okeanos-projects/")

        # Assert the response status code.
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert the structure of the response.
        self.assertIn('status', response.data)
        self.assertIn('data', response.data)

        self.assertIn('code', response.data['status'])
        self.assertIn('short_description', response.data['status'])

        # Assert the contents of the response.
        self.assertEqual(response.data['status']['code'], status.HTTP_200_OK)
        self.assertEqual(response.data['status']['short_description'],
                         ResponseMessages.short_descriptions['user_okeanos_projects'])

        self.assertEqual(response.data['data'], [{'id': 1, 'name': "name1"},
                                                 {'id': 2, 'name': "name2"}])
