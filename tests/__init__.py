# Test directory
import logging
import os
import unittest


def get_suite():
    "Return a unittest.TestSuite."
    import tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir)
    return suite