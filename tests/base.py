# -*- coding: utf-8 -*-

import os
import re
import subprocess
import tempfile
import vimrunner

from tasklib import TaskWarrior, Task
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

        # Create an actual taskrc file where we can write later
        self.taskrc_path = os.path.join(self.dir, "taskrc")
        with open(self.taskrc_path, 'w') as f:
            f.write("#testing taskrc\n")

        self.tw = TaskWarrior(
            data_location=self.dir,
            taskrc_location=self.taskrc_path
        )

        new_tasks = [Task(self.tw, **task_kwargs)
                     for task_kwargs in self.tasks]

        self.tasks = new_tasks
        for task in self.tasks:
            task.save()

    def start_client(self, retry=3):
        try:
            self.client = server.start_gvim()
        except RuntimeError:
            if retry > 0:
                sleep(2)
                self.start_client(client, retry=retry-1)
            else:
                raise

    def configure_global_varialbes(self):
        self.command('let g:taskwiki_measure_coverage="yes"')
        self.command('let g:taskwiki_data_location="{0}"'.format(self.dir))
        self.command('let g:taskwiki_taskrc_location="{0}"'.format(self.taskrc_path))

    def setup(self):
        self.generate_data()
        self.start_client()  # Start client with 3 chances
        self.configure_global_varialbes()
        self.add_plugin('taskwiki')
        self.add_plugin('vimwiki')
        sleep(0.5)
        self.filepath = os.path.join(self.dir, 'testwiki.txt')
        self.client.edit(self.filepath)
        sleep(0.5)
        self.command('set filetype=vimwiki', silent=None)  # TODO: fix these vimwiki loading errors
        sleep(1)  # Give vim some time to load the scripts

    def teardown(self):
        self.client.quit()
        subprocess.call(['killall', 'gvim'])
        sleep(0.5)  # Killing takes some time
        self.tasks = self.__class__.tasks  # Reset the task list

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

    def check_sanity(self, soft=True):
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
            if not soft:
                assert any([scriptfile in line for line in scriptnames])
            elif not any([scriptfile in line for line in scriptnames]):
                return False

        # Assert only note about Bram being maintainer is in messages
        bramline = u'Messages maintainer: Bram Moolenaar <Bram@vim.org>'
        if not soft:
            assert self.client.command('messages') == bramline
        elif not self.client.command('messages') == bramline:
            return False

        # Assert that TW and cache objects exist
        cache_class = self.client.command('py print(cache.__class__.__name__)')
        tw_class = self.client.command(
            'py print(cache.warriors["default"].__class__.__name__)')

        if not soft:
            assert tw_class == 'TaskWarrior'
            assert cache_class == 'TaskCache'
        elif tw_class != 'TaskWarrior' or cache_class != 'TaskCache':
            return False

        # Success in the sanity check
        return True

    # Helper function that fills in {uuid} placeholders with correct UUIDs
    def fill_uuid(self, line):
        # Tasks in testing can have only alphanumerical descriptions
        match = re.match(ur'\s*\* \[.\] (?P<desc>[äa-zA-Z0-9 ]*)(?<!\s)', line,
                flags=re.UNICODE)

        if not match:
            return line

        # Find the task and fill in its uuid
        tasks = self.tw.tasks.filter(description=match.group('desc'))
        if tasks:
            # Return {uuid} replaced by short form UUID
            return line.format(uuid=tasks[0]['uuid'].split('-')[0])
        else:
            return line


    def test_execute(self):
        # First, run sanity checks
        success = False

        for i in range(5):
            if self.check_sanity(soft=True):
                success = True
                break
            else:
                self.teardown()
                self.setup()

        if not success:
            self.check_sanity(soft=False)

        # Then load the input
        if self.viminput:
            # Unindent the lines
            lines = [self.fill_uuid(l[4:])
                     for l in self.viminput.strip('\n').splitlines()]
            self.write_buffer(lines)

        # Do the stuff
        self.execute()

        # Check expected output
        if self.vimoutput:
            lines = [
                self.fill_uuid(l[4:])
                for l in self.vimoutput.strip('\n').splitlines()[:-1]
            ]
            assert self.read_buffer() == lines


class MultipleSourceTest(IntegrationTest):

    extra_tasks = []

    def generate_data(self):
        super(MultipleSourceTest, self).generate_data()

        self.extra_dir = tempfile.mkdtemp(dir='/tmp/')

        self.extra_tw = TaskWarrior(
            data_location=self.extra_dir,
            taskrc_location='/'
        )

        extra_tasks = [Task(self.extra_tw, **task_kwargs)
                      for task_kwargs in self.extra_tasks]

        self.extra_tasks = extra_tasks
        for task in self.extra_tasks:
            task.save()

    def configure_global_varialbes(self):
        super(MultipleSourceTest, self).configure_global_varialbes()

        self.client.feedkeys(':let g:taskwiki_extra_warriors={0}'.format(
            {'H': dict(data_location=str(self.extra_dir), taskrc_location='/')}
        ))
        self.client.feedkeys('\<CR>')
        self.client.feedkeys('\<CR>')

    def fill_uuid(self, line):
        # Tasks in testing can have only alphanumerical descriptions
        match = re.match(r'\s*\* \[.\] (?P<desc>[a-zA-Z0-9 ]*)(?<!\s)', line)
        if not match:
            return line

        # Find the task and fill in its uuid
        tasks = self.tw.tasks.filter(description=match.group('desc'))
        extra_tasks = self.extra_tw.tasks.filter(description=match.group('desc'))

        if len(tasks) > 1 or len(extra_tasks) > 1:
            raise RuntimeError("Description '{0}' matches multiple tasks. "
                "Aborting fill_uuid operation.".format(match.group('desc')))

        if tasks:
            # Return {uuid} replaced by short form UUID
            return line.format(uuid=tasks[0]['uuid'].split('-')[0])
        elif extra_tasks:
            return line.format(uuid=tasks[0]['uuid'].split('-')[0])
        else:
            return line

# Mock vim to test vim-nonrelated functions
class MockVim(object):

    class current(object):
        buffer = ['']

    vars = dict()
    warriors = dict()

    def eval(*args, **kwargs):
        return 42

    def reset(self):
        self.current.buffer = ['']
        self.vars.clear()
        self.warriors.clear()


# Mock Cache object
class MockCache(object):
    warriors = {'default': 'default'}
    buffer_has_authority = True

    def __init__(self):
        from taskwiki import store
        self.line = store.LineStore(self)
        self.vwtask = dict()
        self.task = dict()
        self.viewport = dict()

    def reset(self):
        self.warriors.clear()
        self.warriors.update({'default': 'default'})
        self.buffer_has_authority = True

