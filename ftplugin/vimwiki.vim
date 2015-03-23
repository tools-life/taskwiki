let s:plugin_path = escape(expand('<sfile>:p:h:h'), '\')
execute 'pyfile ' . s:plugin_path . '/taskwiki/taskwiki.py'

augroup taskwiki
    " when saving the file sync the tasks from vimwiki to TW
    autocmd!
    execute "autocmd BufWrite *.".expand('%:e')." py WholeBuffer.update_to_tw()"
augroup END

" Split reports commands
command! -nargs=* TaskWikiProjects :py SplitProjects(<q-args>).execute()
command! -nargs=* TaskWikiProjectsSummary :py SplitSummary(<q-args>).execute()
command! -nargs=* TaskWikiBurndownDaily :py SplitBurndownDaily(<q-args>).execute()
command! -nargs=* TaskWikiBurndownMonthly :py SplitBurndownMonthly(<q-args>).execute()
command! -nargs=* TaskWikiBurndownWeekly :py SplitBurndownWeekly(<q-args>).execute()
command! -nargs=* TaskWikiCalendar :py SplitCalendar(<q-args>).execute()
command! -nargs=* TaskWikiGhistoryAnnual :py SplitGhistoryAnnual(<q-args>).execute()
command! -nargs=* TaskWikiGhistoryMonthly :py SplitGhistoryMonthly(<q-args>).execute()
command! -nargs=* TaskWikiHistoryAnnual :py SplitGhistoryAnnual(<q-args>).execute()
command! -nargs=* TaskWikiHistoryMonthly :py SplitGhistoryMonthly(<q-args>).execute()
command! -nargs=* TaskWikiStats :py SplitStats(<q-args>).execute()
command! -nargs=* TaskWikiTags :py SplitTags(<q-args>).execute()

" Commands that operate on tasks in the buffer
command! -range TaskWikiInfo :<line1>,<line2>py SelectedTasks().info()
command! -range TaskWikiLink :<line1>,<line2>py SelectedTasks().link()
command! -range TaskWikiDelete :<line1>,<line2>py SelectedTasks().delete()
command! -range TaskWikiStart :<line1>,<line2>py SelectedTasks().start()
command! -range TaskWikiStop :<line1>,<line2>py SelectedTasks().stop()
command! -range -nargs=* TaskWikiMod :<line1>,<line2>py SelectedTasks().modify(<q-args>)

" Disable <CR> as VimwikIFollowLink
if !hasmapto('<Plug>VimwikiFollowLink')
  nmap <Plug>NoVimwikiFollowLink <Plug>VimwikiFollowLink
endif

nmap <silent><buffer> <CR> :py Mappings.task_info_or_vimwiki_follow_link()<CR>
