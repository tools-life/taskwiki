let s:plugin_path = escape(expand('<sfile>:p:h:h'), '\')
execute 'pyfile ' . s:plugin_path . '/taskwiki/taskwiki.py'

augroup taskwiki
    " when saving the file sync the tasks from vimwiki to TW
    autocmd!
    execute "autocmd BufWrite *.".expand('%:e')." python update_to_tw()"
augroup END

command! -range TaskWikiInfo :<line1>,<line2>py SelectedTasks().info()
command! -range TaskWikiLink :<line1>,<line2>py SelectedTasks().link()
command! -range TaskWikiDelete :<line1>,<line2>py SelectedTasks().delete()
command! -range -nargs=* TaskWikiMod :<line1>,<line2>py SelectedTasks().modify(<q-args>)
