# -*- coding: utf-8 -*-

from unittest import TestCase

from test_data import *

"""

In case tests are not running properly, create manualy dir structure like below and comment 
in setUpClass "TestDropboxAPI.create_env()" and provide filenames for lip01 and lip02 
  
a   ->  b   ->  lip01.txt
                lip10.txt
        c
        d
        lip01.txt
        lip10.txt
"""

class TestDropboxAPI(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestDropboxAPI, cls).setUpClass()
        create_env()

    @classmethod
    def tearDownClass(cls):
        super(TestDropboxAPI, cls).tearDownClass()

    def setUp(self):
        super(TestDropboxAPI, self).setUp()
        self.r = DbxAPI()
        self.lip01 = lip01_tmpfile.name
        self.lip02 = lip10_tmpfile.name

    def test_get_metadata(self):
        result = self.r.get_metadata(remote_dir)
        self.assertEquals(remote_dir, result._get_key("path_display"))

        result = self.r.get_metadata(remote_dir +"/jhkgfadhsg")
        self.assertTrue(result.is_error)
        self.assertTrue(result.is_error_not_found)


    def test_list_folder(self):
        result = self.r.list_folder(remote_dir)
        self.assertEquals(remote_dir, result._get_key("path_display"))
        self.assertTrue(result.has_entry(remote_dir +"/b"))
        result = self.r.list_folder("/")
        self.assertTrue(result.has_entry(remote_dir))

    def test_download(self):
        result = self.r.download(remote_dir +"/lip01.txt")
        self.assertFalse(result.is_error)
        self.assertFalse(result.is_error_not_found)
        f = open(self.lip01, 'r')
        self.assertEquals(f.read(), result.file_handle.read())

    def test_download_seek(self):
        result = self.r.download(remote_dir +"/lip01.txt", 57)
        self.assertFalse(result.is_error)
        self.assertFalse(result.is_error_not_found)
        f = open(self.lip01, 'r')
        r = f.read()
        self.assertEquals(r[57:], result.file_handle.read())

    def test_create_folder(self):
        result = self.r.delete("/test_folder")
        result = self.r.create_folder("/test_folder")
        self.assertEquals("/test_folder", result._get_key("path_display"))
        result = self.r.create_folder("/test_folder")
        self.assertTrue(result.is_error)
        self.assertTrue(result.error_summary.encode('utf-8').startswith("path/conflict/folder"))

    def test_delete_folder(self):
        result = self.r.delete("/non_exist_folder_98764938761")
        self.assertTrue(result.is_error)
        self.assertTrue(result.error_summary.encode('utf-8').startswith("path_lookup/not_found"))
        result = self.r.create_folder("/non_exist_folder_jhsjhgsda")
        self.assertEquals("/non_exist_folder_jhsjhgsda", result._get_key("path_display"))
        result = self.r.delete("/non_exist_folder_jhsjhgsda")
        self.assertFalse(result.is_error)
        self.assertEquals("/non_exist_folder_jhsjhgsda", result._get_key("path_display"))

    def test_upload(self):
        file_name = "/test_upload.txt"
        # Remove if exists
        result = self.r.delete(file_name)
        # Testujemy upload file
        upload_file = FileHandle.new_upload_file_handle(file_name)
        # 50 bytes
        x = "TEST_" * 10
        upload_file.buf = x
        upload_file = self.r.upload(upload_file)
        # another 50 bytes
        y = "FILE_" * 10
        upload_file.buf = y
        upload_file = self.r.upload(upload_file)
        # and last 70 bytes
        z = "UPLOAD_" * 10
        upload_file.buf = z
        upload_file = self.r.upload(upload_file)
        # Finish session
        upload_file = self.r.commit_upload(upload_file)
        # Read file
        result = self.r.download(file_name)
        self.assertFalse(result.is_error)
        self.assertFalse(result.is_error_not_found)
        self.assertEquals(x + y + z, result.file_handle.read())
        result = self.r.delete(file_name)
        self.assertFalse(result.is_error)


    def test_copy(self):
        name = remote_dir +"/b/new_file.txt"
        self.r.delete(name)
        result = self.r.get_metadata(name)
        self.assertTrue(result.is_error_not_found)
        result = self.r.copy(remote_dir +"/lip10.txt",name)
        self.assertEquals(remote_dir +"/b/new_file.txt",result.path)
        result = self.r.get_metadata(name)
        self.assertFalse(result.is_error_not_found)
        self.assertEquals(name,result.path)


    def test_move(self):
        name = remote_dir +"/b/new_file.txt"
        self.r.delete(name)
        result = self.r.copy(remote_dir +"/lip10.txt", remote_dir +"/to_be_moved.txt")
        result = self.r.get_metadata(name)
        self.assertTrue(result.is_error_not_found)
        result = self.r.move(remote_dir +"/to_be_moved.txt",name)
        self.assertEquals(name,result.path)
        result = self.r.get_metadata(name)
        self.assertFalse(result.is_error_not_found)
        self.assertEquals(name,result.path)
