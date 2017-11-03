# RUNME as 'python -m somepackage.tests.__main__'
import unittest
import os

def main():
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    print start_dir
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner()
    runner.run(suite)

#if __name__ == '__main__':
#    main()