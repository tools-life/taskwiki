import os
import tempfile
import vimrunner

from tasklib.task import TaskWarrior, Task

server = vimrunner.Server()

class TestIntegration(object):

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

class TestBurndown(TestIntegration):

    def test_focus_burndown_daily(self):
        self.command("TaskWikiBurndownDaily")
        assert self.command(":py print vim.current.buffer").startswith("<buffer burndown.daily")
        assert "Daily Burndown" in self.read_buffer()[0]

class TestViewports(TestIntegration):

    def test_viewport_filling(self):
        lines = ["=== Work tasks | +work ==="]
        self.write_buffer(lines)
        self.command("w")
        assert self.read_buffer() == [
            "=== Work tasks | +work ===",
            "* [ ] tag work task 1  #{0}".format(self.tasks[3]['uuid'])
            ]

