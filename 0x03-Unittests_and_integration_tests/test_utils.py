#!/usr/bin/env python3
"""
Unit tests for the utils module

This module contains tests for:
- access_nested_map function
- get_json function
- memoize decorator
"""

import unittest
from parameterized import parameterized
from unittest.mock import patch, Mock
from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):
    """
    Test class for access_nested_map function
    """

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2)
    ])
    def test_access_nested_map(self, nested_map, path, expected):
        """
        Test that access_nested_map returns the correct value for given path
        """
        self.assertEqual(access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",), KeyError),
        ({"a": 1}, ("a", "b"), KeyError)
    ])
    def test_access_nested_map_exception(self, nested_map, path,
                                         expected_exception):
        """
        Test that KeyError is raised for invalid paths
        """
        with self.assertRaises(expected_exception):
            access_nested_map(nested_map, path)


class TestGetJson(unittest.TestCase):
    """
    Test class for get_json function
    """

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False})
    ])
    @patch('utils.requests.get')
    def test_get_json(self, test_url, test_payload, mock_requests_get):
        """
        Test that get_json returns the expected result without making
        actual HTTP calls
        """
        mock_response = Mock()
        mock_response.json.return_value = test_payload
        mock_requests_get.return_value = mock_response

        result = get_json(test_url)

        mock_requests_get.assert_called_once_with(test_url)
        self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """
    Test class for memoize decorator
    """

    def test_memoize(self):
        """
        Test that memoize caches the result and only calls the method once
        """
        class TestClass:
            def a_method(self):
                return 42

            @memoize
            def a_property(self):
                return self.a_method()

        test_instance = TestClass()

        with patch.object(test_instance, 'a_method') as mock_a_method:
            mock_a_method.return_value = 42

            result1 = test_instance.a_property
            result2 = test_instance.a_property

            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)
            mock_a_method.assert_called_once()
