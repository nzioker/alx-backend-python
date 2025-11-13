#!/usr/bin/env python3
"""
Unit tests for the client module
"""

import unittest
from parameterized import parameterized
from unittest.mock import patch
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
