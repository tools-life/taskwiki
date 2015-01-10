let s:plugin_path = escape(expand('<sfile>:p:h'), '\')
execute 'pyfile ' . s:plugin_path . '/../autoload/taskwiki.py'

augroup taskwiki
    " when saving the file sync the tasks from vimwiki to TW
    autocmd!
    execute "autocmd BufWrite *.".expand('%:e')." python update_to_tw()"
augroup END
