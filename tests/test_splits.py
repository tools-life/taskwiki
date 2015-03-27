from tests.base import IntegrationTest


class TestBurndown(IntegrationTest):

    def execute(self):
        self.command("TaskWikiBurndownDaily")
        assert self.command(":py print vim.current.buffer", silent=False).startswith("<buffer burndown.daily")
        assert "Daily Burndown" in self.read_buffer()[0]
