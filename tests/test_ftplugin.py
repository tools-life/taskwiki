import os
from tests.base import IntegrationTest


class TestCachePreserved(IntegrationTest):

    def execute(self):
        testfile2 = os.path.join(self.dir, "testwiki2.txt")

        self.command("w", regex="written$", lines=1)
        self.command("w {}".format(testfile2), regex="written$", lines=1)

        self.client.edit(testfile2)

        # check that all buffers have a cache entry
        cache_keys = self.client.eval('py3eval("sorted(cache.caches.keys())")')
        buffers = self.client.eval('py3eval("sorted(b.number for b in vim.buffers)")')
        assert cache_keys == buffers
