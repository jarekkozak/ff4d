# -*- coding: utf-8 -*-
import json
import os
from datetime import datetime
from time import time, mktime

from dateutil import parser


class DbxResponse(object):
    def __init__(self, response, api_result=None, error_code=0, error_summary=None):
        super(DbxResponse, self).__init__()
        self.response = response
        self.api_result = api_result
        self.error_code = error_code
        self.error_summary = error_summary

    def _json_to_dict(self, strdata):
        data = {}
        try:
            data = json.loads(strdata)
        except Exception as e:
            data.update({
                'error': {
                    'error_code': 0,
                    'error_summary': 'Invalid json data',
                    'value': str(strdata)
                },
            })

        if self.error_code != 0:
            data.update({
                'error_http': {
                    'error_code': self.error_code,
                    'error_summary': self.error_summary,
                    'value': str(strdata)
                },
            })

        return data

    def get_download_object(self):
        return DbxObject(data=self._json_to_dict(self.api_result), file_handle=self.response.fp)

    def get_dbx_object(self):
        if self.response is not None:
            data = self._json_to_dict(self.response.read())
        elif self.api_result is not None:
            data = self._json_to_dict(self.api_result)
        else:
            data = self._json_to_dict(None)

        return DbxObject(data=data)

    def get_metadata2(self):
        if self.response is not None:
            data = self._json_to_dict(self.response.read())
            if "metadata" in data:
                data = data["metadata"]
        elif self.api_result is not None:
            data = self._json_to_dict(self.api_result)
        else:
            data = self._json_to_dict(None)
        return DbxObject(data=data)

    # Response has result only if error
    def get_result_if_error(self):
        data = None
        if self.response is not None:
            r = self.response.read()
            if r is not None:
                data = self._json_to_dict(r)
        return DbxObject(data=data if data is not None else {})


class DbxObject(object):
    def __init__(self, data, file_handle=None):
        self.cache_time = 3600
        self.file_handle = file_handle
        self.object = {}
        self.update(data=data)
        self._created = int(time())

    def update(self, data):
        self.object.update(data)

    # Metody prywatne

    # Get entry time and convert it to int
    def _get_time(self, key):
        now = int(time())
        if self._has_key(key):
            t = parser.parse(self._get_key(key))
            now = int(mktime(t.timetuple()))
        return now

    def _has_key(self, key):
        return self.object is not None and key in self.object

    def _return(self, key, value):
        result = self._get_key(key)
        if result is not None:
            return result == value
        return result

    def __str__(self):
        return json.dumps(self.object)

    def get_key(self, key, default=None):
        return self._get_key(key, default)

    def _get_key(self, key, default=None):
        if self._has_key(key):
            return self.object[key]
        return default

    def remove_key(self, key):
        return self.object.pop(key, None)

    @property
    def session_id(self):
        return self._get_key('session_id', None)

    @property
    def is_valid(self):
        return self.object is not None

    @property
    def is_error(self):
        return self._has_key('error') or self._has_key('error_code')

    @property
    def error_summary(self):
        return self._get_key('error_summary')

    @property
    def is_error_not_found(self):
        if not self.is_error:
            return False
        error = DbxObject(data=self._get_key('error'))
        if error.tag != 'path' or error._get_key('path') is None:
            return False
        path = DbxObject(data=error._get_key('path'))
        return path._return('.tag', 'not_found')

    @property
    def is_expired(self):
        return self.valid_until < int(time())

    @property
    def valid_until(self):
        return self._created + self.cache_time

    @property
    def tag(self):
        return self._get_key('.tag')

    @property
    def is_folder(self):
        return self._return('.tag', 'folder')

    @property
    def is_file(self):
        return self._return('.tag', 'file')

    @property
    def is_fs_entry(self):
        return self.is_folder or self.is_file

    @property
    def is_deleted(self):
        return self._return('.tag', 'deleted')

    @property
    def has_more(self):
        return self._return('has_more', True)

    @property
    def cursor(self):
        return self._get_key('cursor')

    @property
    def has_entries(self):
        return self._has_key('entries')

    @property
    def entries(self):
        return self._get_key('entries', [])

    @property
    def has_sub_items(self):
        return self.has_entries

    @property
    def sub_items(self):
        return map(lambda x: DbxObject(x), self.entries)

    @property
    def path(self):
        return self._get_key('path_display')

    @property
    def basename(self):
        return os.path.basename(self.path)

    @property
    def parent_path(self):
        return os.path.dirname(self.path)

    @property
    def server_modified(self):
        return self._get_time("server_modified")

    @property
    def client_modified(self):
        return self._get_time("client_modified")

    @property
    def size(self):
        size = self._get_key('size')
        if size is not None:
            return size
        return 0

    def get_entry(self, path):
        for tmp in self.sub_items:
            if tmp.path == path:
                return tmp
        return None

    def has_entry(self, path):
        if self.get_entry(path) is not None:
            return True
        return False


class FileHandle(object):

    write_cache_size = 4096

    def __init__(self, fsentry, mode='r'):
        self.mode = mode
        self.run = False
        self.lock = False
        self.fh = False
        self.offset = 0
        self.fsentry = fsentry
        self._buf = ''
        self.session_id = ''

    @property
    def is_running(self):
        return self.run == True

    @property
    def is_locked(self):
        return self.lock == True

    def read(self, length):
        try:
            rbytes = self.fh.read(length)
        except Exception as e:
            raise e
        self.offset = self.offset + len(rbytes)
        return rbytes

    @property
    def path(self):
        return self.fsentry.path

    @property
    def is_session_open(self):
        return self.session_id != ""

    # Check if buffer size exceeded max cache size or file is to small to be cached
    @property
    def is_cache_size_exceeded(self):
        return self.buf_size >= self.write_cache_size

    @property
    def buf(self):
        return self._buf

    @buf.setter
    def buf(self, buf):
        self._buf += buf

    # flush is called to empty buffer
    def flush(self):
        self.offset += self.buf_size
        self._buf = ""

    @property
    def buf_size(self):
        return len(self._buf)

    @property
    def upload_status(self):
        return self._upload_status

    @upload_status.setter
    def upload_status(self, upload_status):
        self._upload_status = upload_status

    def update_session_id(self):
        self.session_id = ""
        if self._upload_status is not None:
            self.session_id = self._upload_status.session_id

    @classmethod
    def new_upload_file_handle(self,path):
        return FileHandle(get_new_file_instance(path))

# New empty DBxObject
def get_new_file_instance(path):
    now = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    return DbxObject(data={
        'size': 0,
        'path_display': path,
        'path_lower': path,
        '.tag': 'file',
        'client_modified': now,
        'server_modified': now
    })
