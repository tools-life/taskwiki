# -*- coding: utf-8 -*-
from taskwiki.completion import Completion
from tests.base import IntegrationTest


class FakeTW():
    def __init__(self, projects=[], tags=[]):
        self.version = '2.5.1'
        self.projects = projects
        self.tags = tags

    def execute_command(self, args):
        if args == ["_unique", "project"]:
            return self.projects
        elif args == ["_unique", "tag"]:
            return self.tags
        elif args == ["_columns"]:
            return ["priority", "project", "due", "end"]
        else:
            assert False


class TestCompletionUnit():
    def test_attributes(self):
        c = Completion(FakeTW())
        assert c.modify("") == ["+", "-", "due:", "end:", "priority:", "project:"]
        assert c.modify("pr") == ["priority:", "project:"]
        assert c.modify("pri") == ["priority:"]

    def test_projects(self):
        c = Completion(FakeTW(projects=["aa", "ab", "c"]))
        assert c.modify("proj:") == ["proj:aa", "proj:ab", "proj:c"]
        assert c.modify("proj:a") == ["proj:aa", "proj:ab"]
        assert c.modify("proj:ab") == ["proj:ab"]
        assert c.modify("proj:abc") == []
        assert c.modify("pr:") == []
        assert c.modify("project:ab") == ["project:ab"]

    def test_tags(self):
        c = Completion(FakeTW(tags=["aa", "aa,ab", "c"]))
        assert c.modify("+") == ["+aa", "+ab", "+c"]
        assert c.modify("+a") == ["+aa", "+ab"]
        assert c.modify("+ab") == ["+ab"]
        assert c.modify("+abc") == []

    def test_dates(self):
        c = Completion(FakeTW())
        assert c.modify("end:no") == ["end:now", "end:november"]
        assert c.modify("sch:jan") == ["sch:january"]

    def test_recur(self):
        c = Completion(FakeTW())
        assert c.modify("re:da") == ["re:daily", "re:day"]
        assert c.modify("recur:q") == ["recur:quarterly"]

    def test_omni(self):
        c = Completion(FakeTW())
        assert c.omni_modstring_findstart("* [ ] x") == -1
        assert c.omni_modstring_findstart("* [ ] x --") == -1
        assert c.omni_modstring_findstart("* [ ] x #12345678 --") == -1
        assert c.omni_modstring_findstart("* [ ] x -- #12345678") == -1
        assert c.omni_modstring_findstart("* [ ] x -- ") == 11
        assert c.omni_modstring_findstart("* [ ] x -- x") == 11
        assert c.omni_modstring_findstart("* [ ] x -- xy") == 11
        assert c.omni_modstring_findstart("* [ ] x -- x y") == 13


class TestCompletionIntegMod(IntegrationTest):
    viminput = """
    * [ ] test task 1  #{uuid}
    * [ ] test task 2  #{uuid}
    """

    tasks = [
        dict(description="test task 1", project="ABC"),
        dict(description="test task 2", project="DEF"),
    ]

    def execute(self):
        self.client.feedkeys(":TaskWikiMod\\<Enter>")
        self.client.eval('feedkeys("pro\\<Tab>D\\<Tab>\\<Enter>", "t")')
        self.client.eval('0')  # wait for command completion

        for task in self.tasks:
            task.refresh()

        assert self.tasks[0]['project'] == "DEF"


class TestCompletionIntegOmni(IntegrationTest):
    viminput = """
    * [ ] test task 1  #{uuid}
    """

    tasks = [
        dict(description="test task 1", project="ABC"),
    ]

    def execute(self):
        self.client.feedkeys('1gg')
        self.client.feedkeys('otest task 2 -- pro\\<C-X>\\<C-O>A\\<C-X>\\<C-O>\\<Esc>')
        self.client.eval('0')  # wait for command completion
        self.command("w", regex="written$", lines=1)

        self.client.feedkeys('otest task ☺ -- pro\\<C-X>\\<C-O>A\\<C-X>\\<C-O>\\<Esc>')
        self.client.eval('0')  # wait for command completion
        self.command("w", regex="written$", lines=1)

        task = self.tw.tasks.pending()[1]
        assert task['description'] == 'test task 2'
        assert task['project'] == 'ABC'

        task = self.tw.tasks.pending()[2]
        assert task['description'] == 'test task ☺'
        assert task['project'] == 'ABC'
