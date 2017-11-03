# -*- coding: utf-8 -*-

import logging

from dbxobject import FileHandle, get_new_file_instance

logger = logging.getLogger(__name__)


class ItemCache(object):
    # For cache operations default 120s
    cache_time = 120

    def __init__(self):
        self.flush()
        super(ItemCache, self).__init__()

    def flush(self):
        self._cache = {}

    def is_in_cache(self, path):
        return path in self._cache

    # Remove item from cache.
    def remove(self, path):
        logger.debug('Called removeFromCache() Path: %s', path)
        # Check whether this path exists within cache.
        if not self.is_in_cache(path):
            logger.debug('Path not in cache: %s', path)
            return False

        # Exist in cache
        item = self.get(path)

        # Item is file and parent exist - start removing parent
        if item.is_file and self.is_in_cache(item.parent_path):
            tmp = self.get(item.parent_path)
            if tmp.is_folder:
                self.remove(tmp.path)

        # Check if path has been removed within parent removal stage - keeper point
        if not self.is_in_cache(path):
            logger.debug("Path has been already removed from cache:%s", path)
            return True

        # If is still in cache
        if item.is_folder:
            # Remove folder items from cache.
            logger.debug('Removing childs of path from cache')
            for tmp in item.sub_items:
                tmp_path = tmp.path
                logger.debug('Child removing from cache: %s', tmp_path)
                if self.is_in_cache(tmp_path):
                    self._cache.pop(tmp_path)
        logger.debug('Removing from cache:%s', path)
        self._cache.pop(path)
        return True

    def _add(self, item):
        item.cache_time = self.cache_time
        self._cache[item.path] = item

    # Just cache subitems
    def add(self, item):
        logger.debug("Cache entry:%s", item.path)
        self._add(item)
        for tmp in item.sub_items:
            if not tmp.is_deleted:
                logger.debug("Cache sub-entry:%s", tmp.path)
                self._add(tmp)

    # Get cached item
    def get(self, path):
        return self._cache[path] if path in self._cache else None


class FileHandleCache(object):
    def __init__(self):
        super(FileHandleCache, self).__init__()
        self.openfh = {}

    def is_exist(self, index):
        return index in self.openfh

    # Returns file handle index
    def new_fh(self, mode='r', item=None, path=None):
        if item is None:
            item = get_new_file_instance(path)
        for i in range(1, 8193):
            if i not in self.openfh:
                self.openfh[i] = FileHandle(item, mode)
                return i
        return False

    # Release filehandle if exist
    def release_fh(self, index):
        if not self.is_exist(index):
            return False
        self.openfh.pop(index)
        return True

    def get_fh(self, index):
        return self.openfh[index] if self.is_exist(index) else False

    def is_locked(self, index):
        return self.get_fh(index).is_locked if self.is_exist(index) else False
