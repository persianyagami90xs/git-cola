from __future__ import absolute_import, division, unicode_literals
import os
import unittest

from cola.settings import Settings

from . import helper


class SettingsTestCase(unittest.TestCase):
    """Tests the cola.settings module"""

    def setUp(self):
        Settings.config_path = self._file = helper.tmp_path('settings')
        self.settings = Settings.read()

    def tearDown(self):
        if os.path.exists(self._file):
            os.remove(self._file)

    def test_gui_save_restore(self):
        """Test saving and restoring gui state"""
        settings = Settings.read()
        settings.gui_state['test-gui'] = {'foo': 'bar'}
        settings.save()

        settings = Settings.read()
        state = settings.gui_state.get('test-gui', {})
        self.assertTrue('foo' in state)
        self.assertEqual(state['foo'], 'bar')

    def test_bookmarks_save_restore(self):
        """Test the bookmark save/restore feature"""

        # We automatically purge missing entries so we mock-out
        # git.is_git_worktree() so that this bookmark is kept.

        bookmark = {'path': '/tmp/python/thinks/this/exists', 'name': 'exists'}

        def mock_verify(path):
            return path == bookmark['path']

        settings = Settings.read()
        settings.add_bookmark(bookmark['path'], bookmark['name'])
        settings.save()

        settings = Settings.read(verify=mock_verify)

        bookmarks = settings.bookmarks
        self.assertEqual(len(settings.bookmarks), 1)
        self.assertTrue(bookmark in bookmarks)

        settings.remove_bookmark(bookmark['path'], bookmark['name'])
        bookmarks = settings.bookmarks
        self.assertEqual(len(bookmarks), 0)
        self.assertFalse(bookmark in bookmarks)

    def test_bookmarks_removes_missing_entries(self):
        """Test that missing entries are removed after a reload"""
        # verify returns False so all entries will be removed.
        bookmark = {'path': '.', 'name': 'does-not-exist'}
        settings = Settings.read(verify=lambda x: False)
        settings.add_bookmark(bookmark['path'], bookmark['name'])
        settings.remove_missing_bookmarks()
        settings.save()

        settings = Settings.read()
        bookmarks = settings.bookmarks
        self.assertEqual(len(settings.bookmarks), 0)
        self.assertFalse(bookmark in bookmarks)

    def test_rename_bookmark(self):
        settings = Settings.read()
        settings.add_bookmark('/tmp/repo', 'a')
        settings.add_bookmark('/tmp/repo', 'b')
        settings.add_bookmark('/tmp/repo', 'c')

        settings.rename_bookmark('/tmp/repo', 'b', 'test')

        expect = ['a', 'test', 'c']
        actual = [i['name'] for i in settings.bookmarks]
        self.assertEqual(expect, actual)


if __name__ == '__main__':
    unittest.main()
