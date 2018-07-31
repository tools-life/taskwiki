import os
import atexit
import coverage

class CoverageSaver(object):

    def __init__(self, cov):
        self.cov = cov

    def __call__(self):
        self.cov.stop()
        self.cov.save()


coverage_path = '/tmp/taskwiki-coverage/.coverage.{0}'.format(os.getpid())
cov = coverage.coverage(data_file=coverage_path)
cov.start()

saver = CoverageSaver(cov)
atexit.register(saver)
