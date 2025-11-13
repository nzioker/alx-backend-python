#!/usr/bin/env python3
"""
Unit tests for the client module
"""

import unittest
from parameterized import parameterized
from unittest.mock import patch, PropertyMock
from client import GithubOrgClient


class TestGithubOrgClient(unittest.TestCase):
    """
    Test class for GithubOrgClient
    """

    @parameterized.expand([
        ("google",),
        ("abc",)
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """
        Test that GithubOrgClient.org returns the correct value
        """
        # Create test instance
        test_client = GithubOrgClient(org_name)
        
        # Set up the mock return value
        expected_org_data = {
            "login": org_name, 
            "id": 12345, 
            "repos_url": f"https://api.github.com/orgs/{org_name}/repos"
        }
        mock_get_json.return_value = expected_org_data
        
        # Access the org property (no parentheses due to @memoize decorator)
        result = test_client.org
        
        # Verify get_json was called once with the correct URL
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(expected_url)
        
        # Verify the result matches the expected data
        self.assertEqual(result, expected_org_data)

    def test_public_repos_url(self):
        """
        Test that GithubOrgClient._public_repos_url returns the expected value
        """
        # Known payload to use for mocking
        known_payload = {
            "repos_url": "https://api.github.com/orgs/test-org/repos"
        }
        
        # Use patch as context manager to mock the org property
        with patch('client.GithubOrgClient.org', new_callable=PropertyMock) as mock_org:
            # Configure the mock to return our known payload
            mock_org.return_value = known_payload
            
            # Create test instance
            test_client = GithubOrgClient("test-org")
            
            # Call the _public_repos_url property
            result = test_client._public_repos_url
            
            # Verify the result is the expected repos_url from our payload
            expected_url = "https://api.github.com/orgs/test-org/repos"
            self.assertEqual(result, expected_url)

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """
        Test that GithubOrgClient.public_repos returns the expected list of repos
        """
        # Mock payload for get_json (repos data)
        mock_repos_payload = [
            {"name": "repo1", "license": {"key": "mit"}},
            {"name": "repo2", "license": {"key": "apache-2.0"}},
            {"name": "repo3", "license": None}
        ]
        mock_get_json.return_value = mock_repos_payload
        
        # Mock _public_repos_url property
        with patch('client.GithubOrgClient._public_repos_url',
                  new_callable=PropertyMock) as mock_public_repos_url:
            # Configure the mock to return a test URL
            mock_public_repos_url.return_value = "https://api.github.com/orgs/test-org/repos"
            
            # Create test instance
            test_client = GithubOrgClient("test-org")
            
            # Call public_repos method (without license filter)
            result = test_client.public_repos()
            
            # Expected list of repo names
            expected_repos = ["repo1", "repo2", "repo3"]
            
            # Verify the result matches expected repo names
            self.assertEqual(result, expected_repos)
            
            # Verify get_json was called once with the mocked URL
            mock_get_json.assert_called_once_with("https://api.github.com/orgs/test-org/repos")
            
            # Verify _public_repos_url property was accessed
            mock_public_repos_url.assert_called_once()
