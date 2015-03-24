import sys

# Mock vim to test vim-nonrelated functions
class MockVim(object):

    def eval(*args, **kwargs):
        return 42

sys.modules['vim'] = MockVim()

from taskwiki import util

def test_modstring_to_args():
    assert util.tw_modstring_to_args("") == []
    assert util.tw_modstring_to_args("project:Random") == ["project:Random"]
    assert util.tw_modstring_to_args("project:Random area:admin") == ["project:Random", "area:admin"]
    assert util.tw_modstring_to_args("project:Random +test") == ["project:Random", "+test"]
    assert util.tw_modstring_to_args("project:Random  +test") == ["project:Random", "+test"]
    assert util.tw_modstring_to_args("project:Random    due:now") == ["project:Random", "due:now"]
    assert util.tw_modstring_to_args("project:'Random +test'") == ["project:Random +test"]

def test_modstring_to_kwargs():
    assert util.tw_modstring_to_kwargs("") == {}
    assert util.tw_modstring_to_kwargs("project:Random") == {"project":"Random"}
    assert util.tw_modstring_to_kwargs("project:Random area:admin") == {"project":"Random", "area":"admin"}
    assert util.tw_modstring_to_kwargs("project:Random +test") == {"project":"Random", "tags":["test"]}
    assert util.tw_modstring_to_kwargs("project:Random +test +home") == {"project":"Random", "tags":["test", "home"]}
    assert util.tw_modstring_to_kwargs("project:'Random +test'") == {"project":"Random +test"}

