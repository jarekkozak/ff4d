# -*- coding: utf-8 -*-
import json
from unittest import TestCase
from dbxobject import DbxResponse


class TestDbxResponse(TestCase):
    def test__to_dictionary(self):
        r = DbxResponse(None)
        self.assertEquals({'error': {'error_summary': 'Invalid json data', 'error_code': 0, 'value': 'None'}},
                          r._json_to_dict(None))

    def test_get_download_object(self):
        r = DbxResponse(response=None,
                        api_result='{"error_summary": "path_lookup/not_found/", "error": {".tag": "path_lookup", "path_lookup": {".tag": "not_found"}}}',
                        error_code=409,
                        error_summary="path_lookup/not_found/")

        expected = {'error_summary': 'path_lookup/not_found/',
                    'error_http': {'error_summary': 'path_lookup/not_found/', 'error_code': 409,
                                   'value': '{"error_summary": "path_lookup/not_found/", "error": {".tag": "path_lookup", "path_lookup": {".tag": "not_found"}}}'},
                    'error': {'path_lookup': {'.tag': 'not_found'}, '.tag': 'path_lookup'}}

        self.assertEquals(expected, r.get_dbx_object().object)

    def test_get_dbx_object(self):
        r = DbxResponse(response=None,
                        api_result='{"error_summary": "path_lookup/not_found/", "error": {".tag": "path_lookup", "path_lookup": {".tag": "not_found"}}}',
                        error_code=409,
                        error_summary="path_lookup/not_found/")

        expected = {'error_summary': u'path_lookup/not_found/',
                    'error_http': {'error_summary': 'path_lookup/not_found/', 'error_code': 409,
                                   'value': '{"error_summary": "path_lookup/not_found/", "error": {".tag": "path_lookup", "path_lookup": {".tag": "not_found"}}}'},
                    'error': {'path_lookup': {'.tag': 'not_found'}, '.tag': 'path_lookup'}}

        self.assertEquals(expected, r.get_dbx_object().object)


