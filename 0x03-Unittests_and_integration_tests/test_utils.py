#!/usr/bin/env python3

import unittest
from parameterized import parameterized
from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2)
        ])
    def test_access_nested_map(self, nested_map, path,expected):
        self.assertEqual(access_nested_map(nested_map, path), expected)

    
    @parameterized.expand([
        ({},("a",), KeyError),
        ({"a": 1},("a", "b"), KeyError)
    ])
    def test_access_nested_map_exception(self,nested_map,path, expected):
        with self.assertRaises(expected):
            access_nested_map(nested_map,path)

class TestGetJson(unittest.TestCase):

    @parameterized.expand([
        ("http://example.com",{"payload": True}),
        ("http://holberton.io", {"payload": False})
    ])
    def test_get_json(self, test_url, test_response):
        with patch('utils.requests.get') as mock_requests_get:
            mock_response = Mock()
            mock_response.json.return_value = test_response
            mock_requests_get.return_value = mock_response
            result = get_json(test_url)
            mock_requests_get.assert_called_once_with(test_url)
            self.assertEqual(result, test_response)

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

        # Create an instance of TestClass
        test_instance = TestClass()

        # Mock the a_method to track calls
        with patch.object(test_instance, 'a_method') as mock_a_method:
            # Configure the mock to return 42
            mock_a_method.return_value = 42

            # Access a_property twice (as attribute, NOT as method call)
            result1 = test_instance.a_property  # ← No parentheses!
            result2 = test_instance.a_property  # ← No parentheses!

            # Verify both accesses return the correct result
            self.assertEqual(result1, 42)
            self.assertEqual(result2, 42)

            # Verify a_method was called only once (due to memoization)
            mock_a_method.assert_called_once()
