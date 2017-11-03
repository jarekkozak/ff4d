# -*- coding: utf-8 -*-

import httplib
import json
import logging
import urllib
import urllib2

from dbxobject import DbxResponse, DbxObject

logger = logging.getLogger(__name__)


class DbxRequest(object):
    access_token = None
    default_content_type = "application/json"
    binary_content_type = "application/octet-stream"

    def __init__(self, binary=False, dbx_arg=None, access_token=None, user_agent="apiRequest/tools.schmidt.ps",
                 extra_params=None, content_type="application/json"):
        if access_token is not None:
            self.access_token = access_token
        self.dbx_arg = dbx_arg
        self.user_agent = user_agent
        self.binary = binary
        self.extra_params = extra_params
        self.default_content_type = content_type
        super(DbxRequest, self).__init__()

    def get_headers(self):
        headers = {}
        if self.default_content_type:
            headers.update({"Content-Type": self.default_content_type})
        if self.binary:
            headers.update({"Content-Type": self.binary_content_type})
        if self.access_token is not None:
            headers.update({'Authorization': 'Bearer ' + self.access_token})
        if self.dbx_arg is not None:
            headers.update({"Dropbox-API-Arg": json.dumps(self.dbx_arg)})
        if self.user_agent is not None:
            headers.update({"User-Agent": self.user_agent})
        if self.extra_params is not None:
            headers.update(self.extra_params)
        return headers

    # Function to handle POST API request.
    def post(self, url, args=None, body="", headers=None):
        if headers == None:
            headers = self.get_headers()

        # Add arguments to request string.
        if args != None and len(args) > 0:
            url = url + '?' + urllib.urlencode(args)

        logger.debug("POST url:%s args:%s headers:%s body length:%s" % (url, args, json.dumps(headers), len(body)))

        response = None
        api_result = {}
        # Server not support operation
        error_code = 0
        error_summary = ""
        try:
            req = urllib2.Request(url, data=body, headers=headers)
            response = urllib2.urlopen(req)
            h = response.headers.dict
            if 'dropbox-api-result' in h:
                api_result = h['dropbox-api-result']
        except urllib2.HTTPError as e:
            logger.exception('apiRequest failed. HTTPError: %s', e.code)
            api_result = e.read()
            error_summary = e.msg
            error_code = e.code
        except urllib2.URLError as e:
            logger.error('apiRequest failed. URLError: %s', e.reason)
            raise Exception('apiRequest failed. URLError: %s', e.reason)
        except httplib.HTTPException as e:
            logger.exception('apiRequest failed. HTTPException...')
            raise Exception('apiRequest failed. HTTPException')
        except Exception as e:
            logger.exception('apiRequest failed. Unknown exception... ')
            raise Exception('apiRequest failed. Unknown exception...')

        return DbxResponse(
            response=response,
            api_result=api_result,
            error_code=error_code,
            error_summary=error_summary)

    def __str__(self):
        return json.dumps(self.get_headers())


class DbxAPI(object):
    def get_metadata(self, path):
        """
        Returns Item - metadata object
        :param path:
        :return:
        """
        url = "https://api.dropboxapi.com/2/files/get_metadata"
        args = {'path': path,
                'include_has_explicit_shared_members': False,
                'include_deleted': False,
                'include_media_info': False}
        request = DbxRequest()
        result = request.post(url, body=json.dumps(args))
        logger.debug("Metadata fetched for :%s - %s", path, result)
        return result.get_dbx_object()

    # Get Dropbox content of path.
    def list_folder(self, path, cursor=None):
        # If cursor has been provided
        request = DbxRequest()
        if cursor is not None:
            args = {
                "cursor": cursor
            }
            result = request.post('https://api.dropboxapi.com/2/files/list_folder/continue', body=json.dumps(args))
            return result.get_dbx_object()

        # Check if path is file, in case of file return file metadata
        if path != '/':
            item = self.get_metadata(path)
        else:
            item = DbxObject(data={".tag":"folder"})
            # API2 requirements
            path = ""

        if item.is_folder:
            args = {
                "path": path,
                "include_media_info": True,
                "include_deleted": False,
                "include_has_explicit_shared_members": False,
                "recursive": False
            }
            result = request.post('https://api.dropboxapi.com/2/files/list_folder', body=json.dumps(args))
            item.update(result.get_dbx_object().object)
        return item

    def download(self, path, seek=False):
        url = "https://content.dropboxapi.com/2/files/download"
        args = {
            "path": path
        }

        # add range retrieval request
        extra_params = {}
        if seek != False:
            extra_params = {'Range': 'bytes=' + str(seek) + '-'}

        request = DbxRequest(binary=True, dbx_arg=args, extra_params=extra_params, content_type=None, user_agent=None)

        response = request.post(url)
        logger.debug("Download result is type:%s", response)
        return response.get_download_object()

    # Delete a Dropbox file/directory object.
    def delete(self, path):
        url = "https://api.dropboxapi.com/2/files/delete_v2"
        args = {
            "path": path
        }
        request = DbxRequest()
        result = request.post(url, body=json.dumps(args))
        return result.get_metadata2()

    # Create a Dropboy folder.
    def create_folder(self, path):
        url = "https://api.dropboxapi.com/2/files/create_folder"
        args = {
            "path": path
        }
        request = DbxRequest()
        result = request.post(url, body=json.dumps(args))
        return result.get_dbx_object()

    # Upload file
    def upload(self, upload_file):
        # Start new upload session
        if not upload_file.is_session_open:
            logger.debug("Upload session not started...starting")
            url = "https://content.dropboxapi.com/2/files/upload_session/start"
            args = {
                'close': False
            }
        else:
            logger.debug("Upload session started, session_id:%s", upload_file.session_id)
            # Session is opened
            url = "https://content.dropboxapi.com/2/files/upload_session/append_v2"
            args = {
                'cursor': {
                    'session_id': upload_file.session_id,
                    'offset': upload_file.offset
                },
                'close': False
            }
        request = DbxRequest(binary=True, dbx_arg=args)
        result = request.post(url, body=upload_file.buf)
        # if upload ok flush buffer
        if not upload_file.is_session_open:
            upload_file.upload_status = result.get_dbx_object()
            upload_file.update_session_id()
        else:
            # After append2 we do not expect response if no error
            upload_file.upload_status = result.get_result_if_error()

        if not upload_file.upload_status.is_error:
            upload_file.flush()

        logger.debug("Upload result:%s", upload_file.upload_status)
        return upload_file

    # Commit chunked upload to Dropbox.
    def commit_upload(self, upload_file):
        ####        path = self.dbx_root_path(path)
        url = "https://content.dropboxapi.com/2/files/upload_session/finish"
        args = {'cursor': {
            "session_id": upload_file.session_id,
            "offset": upload_file.offset
        },
            "commit": {
                "path": upload_file.path
            }
        }
        request = DbxRequest(binary=True, dbx_arg=args)
        result = request.post(url)
        upload_file.result = result.get_dbx_object()
        return upload_file

    # Rename a Dropbox file/directory object.
    def move(self, old, new):
        url = "https://api.dropboxapi.com/2/files/move"
        args = {
            "from_path": old,
            "to_path": new,
            "allow_shared_folder": False,
            "autorename": False,
            "allow_ownership_transfer": False
        }
        request = DbxRequest()
        result = request.post(url, body=json.dumps(args))
        return result.get_dbx_object()

    def copy(self, old, new):
        url = "https://api.dropboxapi.com/2/files/copy_v2"
        args = {
            "from_path": old,
            "to_path": new,
            "allow_shared_folder": False,
            "autorename": False,
            "allow_ownership_transfer": False
        }
        request = DbxRequest()
        result = request.post(url, body=json.dumps(args))
        return result.get_metadata2()

