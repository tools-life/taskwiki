let s:plugin_path = escape(expand('<sfile>:p:h'), '\')

exe 'pyfile ' . s:plugin_path . '/../autoload/vimwiki_pytasks.py'
