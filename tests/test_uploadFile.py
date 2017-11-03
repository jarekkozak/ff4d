# -*- coding: utf-8 -*-

from unittest import TestCase
from dbxobject import FileHandle, get_new_file_instance

class TestUploadFile(TestCase):


    def setUp(self):
        super(TestUploadFile, self).setUp()
        self.u = FileHandle(get_new_file_instance("/upload_file"),'w')

    def test_is_session_open(self):
        self.assertFalse(self.u.is_session_open)
        self.u.session_id = "session id"
        self.assertTrue(self.u.is_session_open)

    def test_is_cache_size_exceeded(self):
        self.assertFalse(self.u.is_cache_size_exceeded)
        self.u.write_cache_size = 100
        self.u.buf = "X"*99
        self.assertFalse(self.u.is_cache_size_exceeded)
        self.u.flush()
        self.u.buf = "X" * 100
        self.assertTrue(self.u.is_cache_size_exceeded)

    def test_append(self):
        self.u.buf = "abc"
        self.assertEquals("abc",self.u.buf)
        self.u.buf = "cdf"
        self.assertEquals("abccdf", self.u.buf)

    def test_flush(self):
        self.u.buf= "abc"
        self.assertEquals("abc",self.u.buf)
        self.u.flush()
        self.assertEquals("",self.u.buf)

    def test_buf_size(self):
        self.assertEquals(0,self.u.buf_size)
        self.u.buf = "abc"
        self.assertEquals(3,self.u.buf_size)
        self.u.buf = "abc"
        self.assertEquals(6,self.u.buf_size)
