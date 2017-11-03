# -*- coding: utf-8 -*-

from unittest import TestCase

from ff4d import Dropbox
from fuse import FuseOSError
from test_data import *


class TestDropbox(TestCase):
    lip01 = lip10_remote
    lip10 = lip10_remote
    test_file = remote_dir + '/test_file.txt'
    non_exist_name = remote_dir + '/879615462938476549.txt'

    @classmethod
    def setUpClass(cls):
        super(TestDropbox, cls).setUpClass()
        create_env()


    # Prepare file for test
    def _prepare_file(self):
        api = DbxAPI()
        api.delete(self.test_file)
        api.delete(self.non_exist_name)
        meta = api.copy(self.lip01, self.test_file)
        self.assertEquals(self.test_file, meta.path)
        meta = api.get_metadata(self.non_exist_name)
        self.assertTrue(meta.is_error_not_found)

    def setUp(self):
        super(TestDropbox, self).setUp()
        FileHandle.write_cache_size = 4096
        self.drb = Dropbox(DbxAPI(), '')

    def test_getDropBoxMetadata(self):
        name = "/b/lip10.txt"
        meta = self.drb.getDropboxMetadata(name)
        self.assertEquals(name, meta.path)

        meta1 = self.drb.getDropboxMetadata(name)
        self.assertEquals(name, meta1.path)
        self.assertEquals(meta.valid_until, meta1.valid_until)

    def test_dbx_root_path(self):
        dbx = Dropbox(DbxAPI(), remote_dir +'')
        self.assertEquals(remote_dir +'/b', dbx.dbx_root_path('/b'))
        self.assertEquals(remote_dir +'/b', dbx.dbx_root_path('//b/'))

    def test_mkdir_rmdir(self):
        dbx = Dropbox(DbxAPI(), remote_dir +'')
        self.assertEquals(0, dbx.mkdir('/zzz', 'w'))
        name = remote_dir +'/zzz'
        meta = dbx.getDropboxMetadata(name)
        self.assertEquals(name, meta.path)
        self.assertEquals(0, dbx.rmdir('/zzz'))
        meta = dbx.getDropboxMetadata(name)
        self.assertFalse(meta)

    # Positive test of unlink
    def test_unlink(self):
        self._prepare_file()
        self.assertEquals(0, self.drb.unlink(self.test_file))

    # Now error

    def test_unlink_error(self):
        with self.assertRaises(FuseOSError) as context:
            self.drb.unlink("/non_existent_path_87901ohufloih87014h187hdpjhf87190.txt")
        self.assertTrue('Input/output error' in context.exception)

    def test_rename(self):
        self._prepare_file()
        self.assertEquals(0, self.drb.rename(self.test_file, self.non_exist_name))
        meta = self.drb.getDropboxMetadata(self.non_exist_name)
        self.assertEquals(self.non_exist_name, meta.path)

    def test_rename_error(self):
        with self.assertRaises(FuseOSError) as context:
            self.drb.rename("/non_existent_path_87901ohufloih87014h187hdpjhf87190.txt",
                            "/non_existent_path_87901ohufloih87014h187hdpjhf87190-A.txt")
        self.assertTrue('Input/output error' in context.exception)

    def test_open(self):
        self.assertGreater(self.drb.open(self.lip01, 0), 0)
        meta = self.drb.cache.get(self.lip01)
        self.assertEquals(self.lip01, meta.path)

    def test_create(self):
        new_file = remote_dir +'/new_file'
        self.assertGreater(self.drb.create(new_file, 0), 0)
        meta = self.drb.cache.get(new_file)
        self.assertEquals(new_file, meta.path)

    def test_read(self):
        fh = self.drb.open(self.lip01, 0)
        meta = self.drb.openfh.get_fh(fh)
        r = self.drb.read(meta.path, 10, 0, fh)
        self.assertEquals('Lorem ipsu', r)
        r = self.drb.read(meta.path, 10, 10, fh)
        self.assertEquals('m dolor si', r)
        r = self.drb.read(meta.path, 10, 12, fh)
        self.assertEquals('dolor sit ', r)
        self.assertEquals(0, self.drb.release(self.lip01, fh))

    def test_write(self):
        FileHandle.write_cache_size = 8192
        name = "/a/nn.txt"
        fh = self.drb.create(name, 0)
        self.assertGreater(fh, 0)
        buf = "A" * 4097
        of = self.drb.write(name, buf, 0, fh)
        self.assertEquals(4097, of)
        buf1 = "B" * 4097
        of1 = self.drb.write(name, buf1, 0, fh)
        self.assertEquals(4097, of1)
        buf2 = "X" * 500
        of2 = self.drb.write(name, buf2, 0, fh)
        self.assertEquals(0, self.drb.release(name, fh))
        meta = self.drb.getDropboxMetadata(name)
        self.assertEquals(name, meta.path)
        self.assertEquals(of + of1 + of2, meta.size)

    def test_readdir(self):
        r = self.drb.readdir('/', 0)
        self.assertTrue('a' in r)
        r = self.drb.readdir(remote_dir +'', 0)
        self.assertTrue('lip01.txt' in r)
        self.assertTrue('lip10.txt' in r)

    def test_getattr(self):
        r = self.drb.readdir(remote_dir +'', 0)
        a1 = self.drb.getattr(remote_dir +'/b')
        self.assertEquals(2, a1['st_nlink'])
        a1 = self.drb.getattr(remote_dir +'/lip01.txt')
        self.assertEquals(1, a1['st_nlink'])
