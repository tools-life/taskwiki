import os
import tempfile
import vimrunner

from tasklib.task import TaskWarrior, Task

server = vimrunner.Server()

class IntegrationTest(object):

    input = None
    output = None

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
        self.tasks = [
            Task(self.tw, description="project random task 1", project="Random"),
            Task(self.tw, description="project random task 2", project="Random"),
            Task(self.tw, description="tag home task 1", tags=["home"]),
            Task(self.tw, description="tag work task 1", tags=["work"]),
            Task(self.tw, description="today task 1", due="now"),
        ]

        for task in self.tasks:
            task.save()

    def setup(self):
        self.generate_data()
        self.client = server.start_gvim()
        self.add_plugin('taskwiki')
        self.add_plugin('vimwiki')
        self.command('let g:taskwiki_data_location="{0}"'.format(self.dir))
        self.client.edit(os.path.join(self.dir, 'testwiki.txt'))
        self.command('set filetype=vimwiki')

    def teardown(self):
        self.client.quit()

    def command(self, command):
        return self.client.command(command)

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

        # First, run sanity checks
        self.check_sanity()

        # Then load the input
        if self.input:
            self.write_buffer(input)

        # Do the stuff
        self.execute()

        # Check expected output
        if self.output:
            assert self.read_buffer() == self.output

class TestBurndown(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownDaily")
        assert self.command(":py print vim.current.buffer").startswith("<buffer burndown.daily")
        assert "Daily Burndown" in self.read_buffer()[0]

class TestViewports(IntegrationTest):

    def execute(self):
        lines = ["=== Work tasks | +work ==="]
        self.write_buffer(lines)
        self.command("w")
        assert self.read_buffer() == [
            "=== Work tasks | +work ===",
            "* [ ] tag work task 1  #{0}".format(self.tasks[3]['uuid'])
            ]


class TestSimpleTask(IntegrationTest):

    def execute(self):
        lines = ["* [ ] This is a test task"]
        self.write_buffer(lines)
        self.command("w")

        # Check that only one tasks with this description exists
        matching = self.tw.tasks.filter(description="This is a test task")
        assert len(matching) == 1

        expected = [
            "* [ ] This is a test task  #{0}".format(matching[0]['uuid'])
        ]

        assert expected == self.read_buffer()
