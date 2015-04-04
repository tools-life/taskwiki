import vim
import os

# Start measuring coverage if in testing
if vim.vars.get('taskwiki_measure_coverage'):
    import atexit
    import coverage
    coverage_path = os.path.expanduser('~/taskwiki-coverage/.coverage.{0}'.format(os.getpid()))
    cov = coverage.coverage(data_file=coverage_path)
    cov.start()

    def save_coverage():
        cov.stop()
        cov.save()

    atexit.register(save_coverage)
