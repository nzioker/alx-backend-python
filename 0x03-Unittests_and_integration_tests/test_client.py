#!/usr/bin/env python3
"""
Integration tests for the client module
"""

import unittest
from parameterized import parameterized, parameterized_class
from unittest.mock import patch, Mock
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """Test class for GithubOrgClient"""

    @parameterized.expand([
        ("google",),
        ("abc",)
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test that GithubOrgClient.org returns the correct value"""
        test_client = GithubOrgClient(org_name)

        expected_org_data = {
            "login": org_name,
            "id": 12345,
            "repos_url": f"https://api.github.com/orgs/{org_name}/repos"
        }
        mock_get_json.return_value = expected_org_data

        result = test_client.org

        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, expected_org_data)

    def test_public_repos_url(self):
        """Test GithubOrgClient._public_repos_url returns expected value"""
        known_payload = {
            "repos_url": "https://api.github.com/orgs/test-org/repos"
        }

        with patch('client.GithubOrgClient.org',
                   new_callable=PropertyMock) as mock_org:
            mock_org.return_value = known_payload

            test_client = GithubOrgClient("test-org")
            result = test_client._public_repos_url

            expected_url = "https://api.github.com/orgs/test-org/repos"
            self.assertEqual(result, expected_url)

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Test GithubOrgClient.public_repos returns expected repos"""
        mock_repos_payload = [
            {"name": "repo1", "license": {"key": "mit"}},
            {"name": "repo2", "license": {"key": "apache-2.0"}},
            {"name": "repo3", "license": None}
        ]
        mock_get_json.return_value = mock_repos_payload

        with patch('client.GithubOrgClient._public_repos_url',
                   new_callable=PropertyMock) as mock_public_repos_url:
            mock_url = "https://api.github.com/orgs/test-org/repos"
            mock_public_repos_url.return_value = mock_url

            test_client = GithubOrgClient("test-org")
            result = test_client.public_repos()

            expected_repos = ["repo1", "repo2", "repo3"]
            self.assertEqual(result, expected_repos)

            mock_get_json.assert_called_once_with(mock_url)
            mock_public_repos_url.assert_called_once()

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False)
    ])
    def test_has_license(self, repo, license_key, expected):
        """Test GithubOrgClient.has_license returns expected result"""
        result = GithubOrgClient.has_license(repo, license_key)
        self.assertEqual(result, expected)


@parameterized_class([
    {
        'org_payload': TEST_PAYLOAD[0][0],
        'repos_payload': TEST_PAYLOAD[0][1],
        'expected_repos': TEST_PAYLOAD[0][2],
        'apache2_repos': TEST_PAYLOAD[0][3]
    }
])
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration test class for GithubOrgClient"""

    @classmethod
    def setUpClass(cls):
        """Set up class for integration tests"""
        # Start patcher for requests.get
        cls.get_patcher = patch('requests.get')
        cls.mock_get = cls.get_patcher.start()

        # Define side_effect to return different payloads based on URL
        def side_effect(url):
            """Return appropriate payload based on URL"""
            if url == "https://api.github.com/orgs/google":
                # Return org payload
                mock_response = Mock()
                mock_response.json.return_value = cls.org_payload
                return mock_response
            elif url == cls.org_payload["repos_url"]:
                # Return repos payload
                mock_response = Mock()
                mock_response.json.return_value = cls.repos_payload
                return mock_response
            # Default response
            mock_response = Mock()
            mock_response.json.return_value = {}
            return mock_response

        cls.mock_get.side_effect = side_effect

    @classmethod
    def tearDownClass(cls):
        """Tear down class after integration tests"""
        # Stop the patcher
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Integration test for public_repos without license"""
        test_client = GithubOrgClient("google")
        result = test_client.public_repos()
        self.assertEqual(result, self.expected_repos)

    def test_public_repos_with_license(self):
        """Integration test for public_repos with apache-2.0 license"""
        test_client = GithubOrgClient("google")
        result = test_client.public_repos(license="apache-2.0")
        self.assertEqual(result, self.apache2_repos)
