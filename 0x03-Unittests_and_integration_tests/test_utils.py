#!/usr/bin/env python3

import unittest
from parameterized import parameterized
from utils import access_nested_map


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
