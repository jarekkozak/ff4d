# -*- coding: utf-8 -*-

import copy
import time
from unittest import TestCase

from dbxobject import DbxObject
from test_data import *


class TestDbxObject(TestCase):
    def setUp(self):
        super(TestDbxObject, self).setUp()

    # def test_update(self):
    #     self.fail()
    #
    # def test__get_time(self):
    #     self.fail()
    #
    # def test__has_key(self):
    #     self.fail()
    #
    # def test__return(self):
    #     self.fail()
    #
    # def test_get_key(self):
    #     self.fail()
    #
    # def test_remove_key(self):
    #     self.fail()

    def test_is_valid(self):
        a1 = DbxObject(data_error)
        self.assertTrue(a1.is_valid)

        a2 = DbxObject(data_file)
        self.assertTrue(a2.is_valid)

        a3 = DbxObject(data_folder_metadata)
        self.assertTrue(a3.is_valid)

    def test_is_error(self):
        a2 = DbxObject(data_error_path_not_found)
        self.assertTrue(a2.is_error)
        self.assertTrue(a2.is_error_not_found)

        a2 = DbxObject(data_folder_metadata)
        self.assertFalse(a2.is_error)

        a2 = DbxObject(data_error)
        self.assertTrue(a2.is_error)

        e1 = copy.deepcopy(data_error)
        a2 = DbxObject(e1)
        self.assertTrue(a2.is_error_not_found)
        e1['error']['.tag'] = 'other'
        a2 = DbxObject(e1)
        self.assertFalse(a2.is_error_not_found)

        e1 = copy.deepcopy(data_error)
        a2 = DbxObject(e1)
        self.assertTrue(a2.is_error_not_found)
        e1['error']['path']['.tag'] = 'other'
        a2 = DbxObject(e1)
        self.assertFalse(a2.is_error_not_found)

    def test_error_summary(self):
        a2 = DbxObject(data_error)
        self.assertEquals(a2.error_summary, data_error['error_summary'])

    def test_is_error_not_found(self):
        a2 = DbxObject(data_error_path_not_found)
        self.assertTrue(a2.is_error)
        self.assertTrue(a2.is_error_not_found)

    def test_is_expired(self):
        a2 = DbxObject(data_folder_metadata)
        self.assertFalse(a2.is_expired)
        DbxObject.cache_time = 1
        time.sleep(2)
        self.assertFalse(a2.is_expired)

    # def test_valid_until(self):
    #     self.fail()

    # def test_tag(self):
    #     self.fail()

    def test_is_folder(self):
        a2 = DbxObject(data_file)
        self.assertFalse(a2.is_folder)

        a3 = DbxObject(data_folder_metadata)
        self.assertTrue(a3.is_folder)

    def test_is_file(self):
        a2 = DbxObject(data_file)
        self.assertTrue(a2.is_file)

        a3 = DbxObject(data_folder_metadata)
        self.assertFalse(a3.is_file)

    def test_is_fs_entry(self):
        a3 = DbxObject(data_folder_metadata)
        self.assertTrue(a3.is_fs_entry)
        a2 = DbxObject(data_file)
        self.assertTrue(a2.is_fs_entry)
        a2 = DbxObject(data_error)
        self.assertFalse(a2.is_fs_entry)

    def test_is_deleted(self):
        a2 = DbxObject(data_folder_metadata_deleted)
        self.assertTrue(a2.is_deleted)

        a3 = DbxObject(data_folder_metadata)
        self.assertFalse(a3.is_deleted)

    def test_has_more(self):
        a2 = DbxObject(data_folder_metadata)
        self.assertFalse(a2.has_more)

        a2 = DbxObject(data_folder_entries)
        self.assertTrue(a2.has_more)

        a2 = DbxObject(data_folder_entries_recursive)
        self.assertFalse(a2.has_more)

    def test_cursor(self):
        a2 = DbxObject(data_folder_metadata)
        self.assertIsNone(a2.cursor)

        a2 = DbxObject(data_folder_entries)
        self.assertEqual(a2.cursor, data_folder_entries['cursor'])

    def test_has_entries(self):
        a2 = DbxObject(data_folder_entries)
        self.assertTrue(a2.has_entries)

        a2 = DbxObject(data_file)
        self.assertFalse(a2.has_entries)

    def test_entries(self):
        a2 = DbxObject(data_folder_entries)
        self.assertTrue(a2.has_entries)
        self.assertEquals(3, len(a2.entries))

    def test_has_sub_items(self):
        a2 = DbxObject(data_folder_entries)
        self.assertTrue(a2.has_entries)

        a2 = DbxObject(data_file)
        self.assertFalse(a2.has_entries)

    def test_sub_items(self):
        a2 = DbxObject(data_folder_entries)
        self.assertEquals(3, len(a2.sub_items))

    def test_path(self):
        a2 = DbxObject(data_file)
        self.assertEquals("/test/subfolder/a6w.odt", a2.path)

    def test_basename(self):
        a2 = DbxObject(data_file)
        self.assertEquals("a6w.odt", a2.basename)

    def test_parent_path(self):
        a2 = DbxObject(data_file)
        self.assertEquals("/test/subfolder", a2.parent_path)

    def test_server_modified(self):
        a2 = DbxObject(data_file)
        t = a2.server_modified
        # self.assertEquals(data_file['server_modified'],t.strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertEquals(1505629042, t)

    def test_server_modified_folder(self):
        now = int(time.time())
        a2 = DbxObject(data_folder_entries_recursive)
        t = a2.server_modified
        self.assertGreaterEqual(t, now)

    def test_client_modified(self):
        a2 = DbxObject(data_file)
        t = a2.client_modified
        # self.assertEquals(data_file['client_modified'],t.strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.assertEquals(1505629042, t)

    def test_client_modified_folder(self):
        now = int(time.time())
        a2 = DbxObject(data_folder_entries_recursive)
        t = a2.client_modified
        self.assertGreaterEqual(t, now)

    def test_size(self):
        a2 = DbxObject(data_file)
        self.assertEquals(19754, a2.size)
