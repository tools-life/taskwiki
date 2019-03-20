# -*- coding: utf-8 -*-
from tests.base import IntegrationTest
from time import sleep


class TestDefaultMapping(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [X] test task 1  #{uuid}
    * [X] test task 2  #{uuid}
    """

    tasks = [
            dict(description="test task 1"),
            dict(description="test task 2"),
    ]

    def execute(self):
        self.client.normal('1gg')
        sleep(0.5)

        self.client.feedkeys(r'\\td')
        sleep(0.5)

        self.client.normal('2gg')
        sleep(0.5)

        self.client.normal('V')
        sleep(0.5)

        self.client.feedkeys(r'\\td')
        sleep(0.5)

        for task in self.tasks:
            task.refresh()


class TestSuppressedMapping(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
            dict(description="test task 1"),
            dict(description="test task 2"),
    ]

    def configure_global_varialbes(self):
        super(TestSuppressedMapping, self).configure_global_varialbes()
        self.command('let g:taskwiki_suppress_mappings="yes"')

    def execute(self):
        self.client.normal('1gg')
        sleep(0.5)

        self.client.feedkeys(r'\\td')
        sleep(0.5)

        self.client.normal('2gg')
        sleep(0.5)

        self.client.normal('V')
        sleep(0.5)

        self.client.feedkeys(r'\\td')
        sleep(0.5)

        for task in self.tasks:
            task.refresh()


class TestCustomMapping(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [X] test task 1  #{uuid}
    * [X] test task 2  #{uuid}
    """

    tasks = [
            dict(description="test task 1"),
            dict(description="test task 2"),
    ]

    def configure_global_varialbes(self):
        super(TestCustomMapping, self).configure_global_varialbes()
        self.command('let g:taskwiki_maplocalleader=",t"')

    def execute(self):
        self.client.normal('1gg')
        sleep(0.5)

        self.client.feedkeys(',td')
        sleep(0.5)

        self.client.normal('2gg')
        sleep(0.5)

        self.client.normal('V')
        sleep(0.5)

        self.client.feedkeys(',td')
        sleep(0.5)

        for task in self.tasks:
            task.refresh()


class TestColonRemap(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [X] test task 1  #{uuid}
    * [X] test task 2  #{uuid}
    """

    tasks = [
            dict(description="test task 1"),
            dict(description="test task 2"),
    ]

    def execute(self):
        self.command('nnoremap ; :')
        self.command('nnoremap : ;')
        self.command('vnoremap ; :')
        self.command('vnoremap : ;')

        self.client.normal('1gg')
        sleep(0.5)

        self.client.feedkeys(r'\\td')
        sleep(0.5)

        self.client.normal('2gg')
        sleep(0.5)

        self.client.normal('V')
        sleep(0.5)

        self.client.feedkeys(r'\\td')
        sleep(0.5)

        for task in self.tasks:
            task.refresh()


class TestColonRemapWithCustomMap(IntegrationTest):

    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    vimoutput = """
    * [X] test task 1  #{uuid}
    * [X] test task 2  #{uuid}
    """

    tasks = [
            dict(description="test task 1"),
            dict(description="test task 2"),
    ]

    def configure_global_varialbes(self):
        super(TestColonRemapWithCustomMap, self).configure_global_varialbes()
        self.command('let g:taskwiki_maplocalleader=",t"')

    def execute(self):
        self.command('nnoremap ; :')
        self.command('nnoremap : ;')
        self.command('vnoremap ; :')
        self.command('vnoremap : ;')

        self.client.normal('1gg')
        sleep(0.5)

        self.client.feedkeys(',td')
        sleep(0.5)

        self.client.normal('2gg')
        sleep(0.5)

        self.client.normal('V')
        sleep(0.5)

        self.client.feedkeys(',td')
        sleep(0.5)

        for task in self.tasks:
            task.refresh()
