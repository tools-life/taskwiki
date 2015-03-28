import os
import re
import subprocess
import tempfile
import vimrunner

from tasklib.task import TaskWarrior, Task
from time import sleep

server = vimrunner.Server()

class IntegrationTest(object):

    viminput = None
    vimoutput = None
    tasks = []

    def add_plugin(self, name):
        plugin_base = os.path.expanduser('~/.vim/bundle/')
        plugin_path = os.path.join(plugin_base, name)
        self.client.add_plugin(plugin_path)

    def write_buffer(self, lines, position=0):
        result = self.client.write_buffer(position + 1, lines)
        assert result == u"0"

    def read_buffer(self, start=0, end=1000):
        return self.client.read_buffer(
            unicode(start+1),
            unicode(end+1)
            ).splitlines()


    def generate_data(self):
        self.dir = tempfile.mkdtemp(dir='/tmp/')
        self.tw = TaskWarrior(data_location=self.dir)

        new_tasks = [Task(self.tw, **task_kwargs)
                     for task_kwargs in self.tasks]

        self.tasks = new_tasks
        for task in self.tasks:
            task.save()

    def setup(self):
        self.generate_data()
        self.client = server.start_gvim()
        self.command('let g:taskwiki_measure_coverage="yes"')
        self.command('let g:taskwiki_data_location="{0}"'.format(self.dir))
        self.add_plugin('taskwiki')
        self.add_plugin('vimwiki')
        self.filepath = os.path.join(self.dir, 'testwiki.txt')
        self.client.edit(self.filepath)
        self.command('set filetype=vimwiki', silent=None)  # TODO: fix these vimwiki loading errors
        sleep(1)  # Give vim some time to load the scripts

    def teardown(self):
        self.client.quit()
        subprocess.call(['killall', 'gvim'])

    def command(self, command, silent=True, regex=None, lines=None):
        result = self.client.command(command)

        # Specifying regex or lines cancels expectations of silence
        if regex or lines:
            silent = False

        # For silent commands, there should be no output
        if silent is not None:
            assert silent == bool(not result)

            # Multiline-evaluate the regex
            if regex:
                assert re.search(regex, result, re.MULTILINE)

            if lines:
                assert lines == len(result.splitlines())

        return result

    def check_sanity(self):
        """
        Makes sanity checks upon the vim instance.
        """

        # Assert all the important files were loaded
        scriptnames = self.client.command('scriptnames').splitlines()
        expected_loaded_files = [
            'vimwiki/autoload/vimwiki/base.vim',
            'vimwiki/ftplugin/vimwiki.vim',
            'vimwiki/autoload/vimwiki/u.vim',
            'vimwiki/syntax/omnipresent_syntax.vim',
            'vimwiki/syntax/vimwiki.vim',
            'taskwiki/ftplugin/vimwiki.vim',
        ]

        # Do a partial match for each line from scriptnames
        for scriptfile in expected_loaded_files:
            assert any([scriptfile in line for line in scriptnames])

        # Assert only note about Bram being maintainer is in messages
        bramline = u'Messages maintainer: Bram Moolenaar <Bram@vim.org>'
        assert self.client.command('messages') == bramline

        # Assert that TW and cache objects exist
        tw_class = self.client.command('py print(tw.__class__.__name__)')
        cache_class = self.client.command('py print(cache.__class__.__name__)')

        assert tw_class == 'TaskWarrior'
        assert cache_class == 'TaskCache'

    def test_execute(self):

        # Helper function that fills in {uuid} placeholders with correct UUIDs
        def fill_uuid(line):
            # Tasks in testing can have only alphanumerical descriptions
            match = re.match(r'\s*\* \[.\] (?P<desc>[a-zA-Z0-9 ]*)(?<!\s)', line)
            if not match:
                return line

            # Find the task and fill in its uuid
            tasks = self.tw.tasks.filter(description=match.group('desc'))
            if tasks:
                # Return {uuid} replaced by short form UUID
                return line.format(uuid=tasks[0]['uuid'].split('-')[0])
            else:
                return line

        # First, run sanity checks
        self.check_sanity()

        # Then load the input
        if self.viminput:
            # Unindent the lines
            lines = [fill_uuid(l[4:])
                     for l in self.viminput.strip('\n').splitlines()]
            self.write_buffer(lines)

        # Do the stuff
        self.execute()

        # Check expected output
        if self.vimoutput:
            lines = [fill_uuid(l[4:])
                     for l in self.vimoutput.strip('\n').splitlines()
                     if l[4:]]
            assert self.read_buffer() == lines
