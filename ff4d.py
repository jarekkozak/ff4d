#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Sascha Schmidt <sascha@schmidt.ps> (author)
# http://blog.schmidt.ps
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Error codes: http://docs.python.org/2/library/errno.html

from __future__ import with_statement

import argparse
import json
import logging
import os
import pwd
import sys
import traceback
from errno import *
from stat import S_IFDIR, S_IFREG
from time import time, sleep

from cache import FileHandleCache, ItemCache
from dbxapi import DbxRequest, DbxAPI
from dbxobject import FileHandle
from fuse import FUSE, FuseOSError, Operations

logger = logging.getLogger(__name__)
rawlogger = logging.getLogger(__name__)


##################################
# Class: FUSE Dropbox operations #
##################################
class Dropbox(Operations):
    root_folder = None

    def __init__(self, dbxApi, root_folder=None):
        self.ar = dbxApi
        self.cache = ItemCache()
        self.openfh = FileHandleCache()
        self.root_folder = root_folder

    # Get metadata for a file or folder from the Dropbox API or local cache.
    # Deep do sprawdzenia
    def getDropboxMetadata(self, path, deep=False):
        logger.debug('Get metadata deep:%s, path:%s', deep, path)
        item = self.cache.get(path)
        if item is not None:
            logger.debug('Found cached metadata for: %s', path)
            # Force deep check in case of directory, expired or deep=True
            if (item.is_folder and item.is_expired) or (deep == True and not item.has_entries):
                # Set temporary hash value for directory non-deep cache entry.
                logger.debug('Metadata directory deepcheck deep:%s, expired:%s, path:%s', deep, item.is_expired, path)
                self.cache.remove(path)
                # Get fresh data
                item = self.ar.list_folder(path)
                if item.is_error or item.is_deleted:
                    logging.exception('Error occured(%s) or entry has been deleted(%s) for %s.', item.is_error,
                                      item.is_deleted, path)
                    return False
                logger.debug('Updating local cache for %s', path)
                # Cache new data.
                self.cache.add(item)
            return item

        # No cached data found, do an Dropbox API request to fetch the metadata.
        logger.debug('No cached metadata for:%s', path)
        try:
            # If the parent path already exists, this path (file/dir) does not exist.
            baseEntry = self.cache.get(os.path.dirname(path))
            if baseEntry is not None and baseEntry.is_folder:
                logger.debug('Basepath %s exists in cache for:%s', baseEntry.path, path)
                return False
            # Get item metadata from dropbox
            item = self.ar.list_folder(path)
            logger.debug("List folder for path %s, Item %s:", path, item)
            # If path does not exists error info is returned or file/older has been deleted
            if item.is_error or item.is_deleted:
                return False
        except Exception as e:
            # Unexpected situation
            logger.error('Could not fetch metadata for: %s', path)
            logger.debug(e, exc_info=True)
            raise FuseOSError(EREMOTEIO)
        # Cache metadata if user wants to use the cache.
        self.cache.add(item)
        return item

    #########################
    # Filesystem functions. #
    #########################

    # Modify path to have full dropbox app path
    def dbx_root_path(self, path):
        return os.path.abspath(self.root_folder + path.encode('utf-8'))

    def mkdir(self, path, mode):
        path = self.dbx_root_path(path)
        logger.debug('Called: mkdir() - Path:%s', path)
        item = self.ar.create_folder(path)
        if item.is_error:
            logger.error('Could not create folder: %s ', item.error_summary)
            raise FuseOSError(EIO)
        # Remove outdated parent folder data from cache.
        self.cache.remove(item.parent_path)
        return 0

    # Remove a directory.
    def rmdir(self, path):
        path = self.dbx_root_path(path)
        logger.debug('Called: rmdir() - Path:%s', path)
        item = self.ar.delete(path)
        if item.is_error:
            logger.error('Could not delete folder:%s', item.error_summary)
            raise FuseOSError(EIO)
        # Remove outdated data from cache.
        self.cache.remove(item.path)
        self.cache.remove(item.parent_path)
        return 0

    # Remove a file.
    def unlink(self, path):
        logger.debug('Called: unlink() - Path: %s', path)
        return self.rmdir(path)

    # Rename a file or directory.
    def rename(self, old, new):
        old = self.dbx_root_path(old)
        new = self.dbx_root_path(new)
        logger.debug('Called: rename() - Old:%s New:%s', old, new)
        item = self.ar.move(old, new)
        if item.is_error:
            logger.error('Could not rename object: %s', item.error_summary)
            raise FuseOSError(EIO)
        # Remove outdated data from cache.
        self.cache.remove(old)
        self.cache.remove(os.path.basename(new))
        return 0

    # Open a filehandle.
    def open(self, path, flags):
        path = self.dbx_root_path(path)
        logger.debug('Called: open() - Path:%s Flags:%s', path, flags)
        # Validate flags.
        if flags & os.O_APPEND:
            logger.debug('O_APPEND mode not supported for open()')
            raise FuseOSError(EOPNOTSUPP)
        meta = self.getDropboxMetadata(path)
        if meta == False:
            logger.debug('Path does not exist:%s', path)
            raise FuseOSError(EOPNOTSUPP)

        fh = self.openfh.new_fh(mode='r', item=meta)
        logger.debug('Returning unique filehandle: %s', fh)
        return fh

    # Create a file.
    def create(self, path, mode):
        path = self.dbx_root_path(path)
        logger.debug('Called: create() - Path:%s  Mode:%s', path, mode)
        fh = self.openfh.new_fh(path=path, mode='w')
        self.cache.add(self.openfh.get_fh(fh).fsentry)
        logger.debug('Returning unique filehandle: %s', fh)
        return fh

    # Read data from a remote filehandle.
    def read(self, path, length, offset, fh):
        path = self.dbx_root_path(path)
        # Get filehandle
        remote_file = self.openfh.get_fh(fh)
        # Wait while this function is not threadable.
        while remote_file.is_locked:
            pass

        logger.debug('Called: read() - Path:%s Length: %s Offset: %s  FH: %s', path, length, offset, fh)
        logger.debug('Expected offset: %s', remote_file.offset)

        if remote_file.fh == False or remote_file.offset != offset:
            # Remote file has not been eopened yet or eoffset is differ
            item = self.ar.download(path, offset)
            if item.is_error:
                logger.error('Could not open remote file: %s, error:%s', path, item.error_summary)
                raise FuseOSError(EIO)
            remote_file.fh = item.file_handle

        rbytes = None
        try:
            rbytes = remote_file.fh.read(length)
            remote_file.offset = offset + len(rbytes)
        except Exception as e:
            logger.error('Could not read data from remotefile')
            logger.error(e, exc_info=True)
            raise FuseOSError(EIO)

        logger.debug('Read bytes from remote source: %s', len(rbytes))
        remote_file.lock = False
        # remote_file.offset = offset + len(rbytes)
        return rbytes

    # Write data to a filehandle.
    def write(self, path, buf, offset, fh):
        path = self.dbx_root_path(path)
        logger.debug('Called: write() - Path: %s Offset:%s FH:%s', path, offset, fh)
        logger.debug('Buffer size %s', len(buf))
        remote_file = self.openfh.get_fh(fh)
        if remote_file == False:
            raise FuseOSError(EIO)
        remote_file.buf = buf
        # Check for the beginning of the file.
        if remote_file.is_cache_size_exceeded:
            if remote_file.is_session_open:
                logger.debug('Cache exceeds configured write_cache. Uploading...')
            else:
                logger.debug('Uploading first chunk to Dropbox...')
            result = self.ar.upload(remote_file)
            if result.upload_status.is_error:
                logger.exception('Could not write to remote file: %s', path)
                raise FuseOSError(EIO)
        else:
            logger.debug('Buffer does not exceed configured write_cache. Caching...')
        # return size of written or cached data
        return len(buf)

    # Release (close) a filehandle.
    def release(self, path, fh):
        path = self.dbx_root_path(path)
        logger.debug('Called: release() - Path:%s FH%s', path, fh)
        remote_file = self.openfh.get_fh(fh)
        if remote_file == False:
            raise FuseOSError(EIO)
        #Release handle whatever happens handle is released
        logger.debug('Released filehandle: ' + str(fh))
        self.openfh.release_fh(fh)
        if (remote_file.mode == 'w' and remote_file.buf_size > 0) or remote_file.is_session_open:
            #Remove from cache
            self.cache.remove(remote_file.path)
            try:
                if remote_file.buf_size > 0:
                    result = self.ar.upload(remote_file)
                    if result.upload_status.is_error:
                        raise Exception()
                result = self.ar.commit_upload(remote_file)
                if result.upload_status.is_error:
                    raise Exception()
            except Exception as e:
                self.cache.remove(remote_file.path)
                logger.exception('Could not write to remote file: %s', path)
                raise FuseOSError(EIO)
            logger.debug('Finishing upload to Dropbox')
        # Remove outdated data from cache if handle was opened for writing.
        return 0

    # Truncate a file to overwrite it.
    def truncate(self, path, length, fh=None):
        path = self.dbx_root_path(path)
        logger.debug('Called: truncate() - Path: ' + path + " Size: " + str(length))
        return 0

    # List the content of a directory.
    def readdir(self, path, fh):
        path = self.dbx_root_path(path)
        logger.debug('Called: readdir() - Path: ' + path)

        # Fetch folder informations.
        fusefolder = ['.', '..']

        metadata = self.getDropboxMetadata(path, True)
        if metadata == False:
            raise FuseOSError(ENOENT)

        # Loop through the Dropbox API reply to build fuse structure.
        for item in metadata.sub_items:
            # Append entry to fuse foldercontent.
            folderitem = item.basename
            fusefolder.append(folderitem)

        logger.debug("fusefolder:" + str(fusefolder))

        # Loop through the folder content.
        for item in fusefolder:
            yield item

    # Get properties for a directory or file.
    def getattr(self, path, fh=None):
        path = self.dbx_root_path(path)

        logger.debug('Called: getattr() - Path:%s', path)

        # Get userid and groupid for current user.
        uid = pwd.getpwuid(os.getuid()).pw_uid
        gid = pwd.getpwuid(os.getuid()).pw_gid

        # Check wether data exists for item.
        item = self.getDropboxMetadata(path)
        if item == False:
            logger.debug("Entry's metadata not found - Path:%s", path)
            raise FuseOSError(ENOENT)

        now = int(time())
        modified = int(item.server_modified)

        if item.is_folder:
            # Get st_nlink count for directory.
            properties = dict(
                st_mode=S_IFDIR | 0755,
                st_size=item.size,
                st_ctime=modified,
                st_mtime=modified,
                st_atime=now,
                st_uid=uid,
                st_gid=gid,
                st_nlink=2
            )
            logger.debug(
                'Returning properties for directory:%s (%s)', path, properties)
            return properties

        # Regular file
        properties = dict(
            st_mode=S_IFREG | 0755,
            st_size=item.size,
            st_ctime=modified,
            st_mtime=modified,
            st_atime=now,
            st_uid=uid,
            st_gid=gid,
            st_nlink=1,
        )
        logger.debug('Returning properties for file:%s (%s)', path, properties)
        return properties

        # Flush filesystem cache. Always true in this case.

    def fsync(self, path, fdatasync, fh):
        path = self.dbx_root_path(path)
        logger.debug('Called: fsync() - Path:%s', path)


###########################
# Class: API authorization#
###########################
class apiAuth:
    def __init__(self):
        self.access_token = False
        self.apiRequest = apiRequest()
        logger.debug('Initialzed apiAuth')

    # Get code for polling.
    def getCode(self, provider, appkey):
        logger.debug('Trying to fetch apiAuth code: ' + provider + ' ' + appkey)
        try:
            args = {'get_code': '', 'provider': provider, 'appkey': appkey}
            result = self.apiRequest.get("https://tools.schmidt.ps/authApp", args)
            data = json.loads(result)
        except Exception as e:
            logger.debug('Failed to fetch apiAuth code', traceback.format_exc())
            return None

        if 'error' in data:
            logger.debug('Error in reply of apiAuth code-request')
            return None

        logger.debug('Got valid apiAuth code: ' + str(data['code']))
        return data['code']

    # Poll code and wait for result.
    def pollCode(self, code):
        loop = True
        print "Waiting for authorization..."
        while loop == True:
            args = {'poll_code': code}
            result = self.apiRequest.get("https://tools.schmidt.ps/authApp", args)
            data = json.loads(result)

            if 'error' in data:
                return False

            if data['state'] == 'invalid':
                return None
            if data['state'] == 'valid':
                return data['authkey']
            sleep(1)
        return False


#####################
# Global functions. #
#####################

# Let the user authorize this application.
def getAccessToken():
    dropbox_appkey = "fg7v60fm9f5ud7n"
    sandbox_appkey = "nstd2c6lbyj4z9b"

    print ""
    print "Please choose which permission this application will request:"
    print "Enter 'd' - This application will have access to your whole"
    print "            Dropbox."
    print "Enter 's' - This application will just have access to its"
    print "            own application folder."
    print ""
    validinput = False
    while validinput == False:
        perm = raw_input("Please enter permission key: ").strip()
        if perm.lower() == 'd' or perm.lower() == 's':
            validinput = True

    appkey = ""
    if perm.lower() == 'd':
        appkey = "fg7v60fm9f5ud7n"
    if perm.lower() == 's':
        appkey = "nstd2c6lbyj4z9b"

    aa = apiAuth()
    code = aa.getCode('dropbox', appkey)
    if code is not None:
        print ""
        print "Please visit http://tools.schmidt.ps/authApp and use the following"
        print "code to authorize this application: " + str(code)
        print ""

        authkey = aa.pollCode(code)
        if authkey != False and authkey != None:
            print "Thanks for granting permission\n"
            return authkey

        if authkey == None:
            print "Rejected permission"

        if authkey == False:
            print "Authorization request expired"
    else:
        print "Failed to start authorization process"

    return False


##############
# Main entry #
##############
# Global variables.
DbxAPI.access_token = False
ItemCache.cache_time = 120  # Seconds
FileHandle.write_cache_size = 4194304  # Bytes
use_cache = False
allow_other = False
allow_root = False
debug = False
debug_raw = False
debug_fuse = False
root_dir = None

if __name__ == '__main__':

    # logger.setLevel(logging.INFO)

    print('********************************************************')
    print('* FUSE Filesystem 4 Dropbox                            *')
    print('*                                                      *')
    print('* Copyright 2014                                       *')
    print('* Sascha Schmidt <sascha@schmidt.ps>                   *')
    print('*                                                      *')
    print('* https://github.com/realriot/ff4d/blob/master/LICENSE *')
    print('********************************************************')
    print('')

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='Show debug output', action='store_true', default=False)
    parser.add_argument('-dr', '--debug-raw', help='Show raw debug output', action='store_true', default=False)
    parser.add_argument('-df', '--debug-fuse', help='Show FUSE debug output', action='store_true', default=False)

    # Mutual exclusion of arguments.
    atgroup = parser.add_mutually_exclusive_group()
    atgroup.add_argument('-ap', '--access-token-perm', help='Use this access token permanently (will be saved)',
                         default=False)
    atgroup.add_argument('-at', '--access-token-temp',
                         help='Use this access token only temporarily (will not be saved)', default=False)

    parser.add_argument('-ao', '--allow-other', help='Allow other users to access this FUSE filesystem',
                        action='store_true', default=False)
    parser.add_argument('-ar', '--allow-root', help='Allow root to access this FUSE filesystem', action='store_true',
                        default=False)
    parser.add_argument('-ct', '--cache-time', help='Cache Dropbox data for X seconds (120 by default)', default=120,
                        type=int)
    parser.add_argument('-wc', '--write-cache',
                        help='Cache X bytes (chunk size) before uploading to Dropbox (4 MB by default)',
                        default=4194304, type=int)

    #parser.add_argument('-rt','--root-dir', help='Dropbox directory to be mounted (Default /)',action='store_true',default='')
    parser.add_argument('-rt', '--root-dir', help='Dropbox app directory to be mounted (default is / app dir)', default='')


    parser.add_argument('-bg', '--background', help='Pushes FF4D into background', action='store_false', default=True)


    parser.add_argument('mountpoint', help='Mount point for Dropbox source')

    args = parser.parse_args()

    # Set variables supplied by commandline.
    ItemCache.cache_time = args.cache_time
    FileHandle.write_cache_size = args.write_cache
    allow_other = args.allow_other
    allow_root = args.allow_root
    debug = args.debug
    debug_raw = args.debug_raw
    debug_fuse = args.debug_fuse

    # Check ranges and values of given arguments.
    if ItemCache.cache_time < 0:
        logger.error('Only positive values for cache-time are possible')
        sys.exit(-1)
    if FileHandle.write_cache_size < 4096:
        logger.error('The minimum write-cache has a size of 4096 Bytes')
        sys.exit(-1)

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    if debug:
        logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    else:
        logging.basicConfig(format=FORMAT, level=logging.INFO)

    # Check wether the mountpoint is a valid directory.
    root_dir = args.root_dir
    mountpoint = args.mountpoint
    if not os.path.isdir(mountpoint):
        logger.error('Given mountpoint is not a directory.')
        sys.exit(-1)

    # Check for an existing configuration file.
    try:
        scriptpath = os.path.dirname(sys.argv[0])
        f = open(scriptpath + '/ff4d.config', 'r')
        access_token = f.readline()
        logger.debug('Got accesstoken from configuration file: ' + str(access_token))
    except Exception as e:
        pass

    # Check wether the user gave an Dropbox access_token as argument.
    if args.access_token_perm != False:
        logger.debug('Got permanent accesstoken from command line: ' + args.access_token_perm)
        access_token = args.access_token_perm
    if args.access_token_temp != False:
        logger.debug('Got temporary accesstoken from command line: ' + args.access_token_temp)
        access_token = args.access_token_temp

    # Check the need to fetch a new access_token.
    if access_token == False:
        logger.info('No accesstoken available. Fetching a new one.')
        access_token = getAccessToken()
        logger.debug('Got accesstoken from user input: ' + str(access_token))

    # Check wether an access_token exists.
    if access_token == False:
        logger.error('No valid accesstoken available. Exiting.')
        sys.exit(-1)

    # Validate access_token.
    DbxRequest.access_token = access_token
    ar = DbxRequest()
    account_info = ''
    try:
        account_info = ar.post('https://api.dropboxapi.com/2/users/get_current_account', body=json.dumps(None))
    except Exception as e:
        logger.error('Could not talk to Dropbox API.')
        logger.error(e, exc_info=True)
        sys.exit(-1)

    # Save valid access token to configuration file.
    if args.access_token_temp == False:
        try:
            scriptpath = os.path.dirname(sys.argv[0])
            f = open(scriptpath + '/ff4d.config', 'w')
            f.write(access_token)
            f.close()
            os.chmod(scriptpath + '/ff4d.config', 0600)
            logger.debug('Wrote accesstoken to configuration file.\n')
        except Exception as e:
            logger.error('Could not write configuration file.')
            logger.error(e, exc_info=True)

    # Everything went fine and we're authed against the Dropbox api.
    # print "Welcome " + account_info['name']['display_name']
    # print "Space used: " + str(account_info['quota_info']['normal'] / 1024 / 1024 / 1024) + " GB"
    # print "Space available: " + str(account_info['quota_info']['quota'] / 1024 / 1024 / 1024) + " GB"
    print ""
    print "Starting FUSE..."

    try:
        FUSE(Dropbox(DbxAPI(), root_folder=root_dir), mountpoint, foreground=args.background, debug=debug_fuse,
             sync_read=True,
             allow_other=allow_other, allow_root=allow_root)
    except Exception as e:
        logger.error('Failed to start FUSE...')
        logger.error(e, exc_info=True)
        sys.exit(-1)
