from time import sleep
from tests.base import IntegrationTest, MultipleSourceTest


class TestSimpleColorAssigment(IntegrationTest):

    def configure_global_varialbes(self):
        super(TestSimpleColorAssigment, self).configure_global_varialbes()
        self.command('let g:taskwiki_source_tw_colors="yes"')

        # Also setup TW config at this point
        self.tw.execute_command(['config', 'color.active', 'color2'])

    def execute(self):
        assert "ctermfg=2" in self.command("hi TaskWikiTaskActive", silent=False)
