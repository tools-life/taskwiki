" Check VIM version
if version < 704
  echoerr "Taskwiki requires at least Vim 7.4. Please upgrade your environment."
  finish
endif

" Check presence of the python support
if ! has("python")
  echoerr "Taskwiki requires Vim compiled with the Python support."
  finish
endif

" Disable taskwiki if taskwiki_disable variable set
if exists("g:taskwiki_disable")
  finish
endif

" Determine the plugin path
let s:plugin_path = escape(expand('<sfile>:p:h:h'), '\')

" Run the measure parts first, if desired
if exists("g:taskwiki_measure_coverage")
  execute 'pyfile ' . s:plugin_path . '/taskwiki/coverage.py'
endif

" Execute the main body of taskwiki source
execute 'pyfile ' . s:plugin_path . '/taskwiki/taskwiki.py'

augroup taskwiki
    autocmd!
    " Update to TW upon saving
    execute "autocmd BufWrite *.".expand('%:e')." TaskWikiBufferSave"
    " Save and load the view to preserve folding, if desired
    if !exists('g:taskwiki_dont_preserve_folds')
      execute "autocmd BufWinLeave *.".expand('%:e')." mkview"
      execute "autocmd BufWinEnter *.".expand('%:e')." silent loadview"
    endif
augroup END

" Global update commands
command! -nargs=* TaskWikiBufferSave :py WholeBuffer.update_to_tw()
command! -nargs=* TaskWikiBufferLoad :py WholeBuffer.update_from_tw()

" Split reports commands
command! -nargs=* TaskWikiProjects :py SplitProjects(<q-args>).execute()
command! -nargs=* TaskWikiProjectsSummary :py SplitSummary(<q-args>).execute()
command! -nargs=* TaskWikiBurndownDaily :py SplitBurndownDaily(<q-args>).execute()
command! -nargs=* TaskWikiBurndownMonthly :py SplitBurndownMonthly(<q-args>).execute()
command! -nargs=* TaskWikiBurndownWeekly :py SplitBurndownWeekly(<q-args>).execute()
command! -nargs=* TaskWikiCalendar :py SplitCalendar(<q-args>).execute()
command! -nargs=* TaskWikiGhistoryAnnual :py SplitGhistoryAnnual(<q-args>).execute()
command! -nargs=* TaskWikiGhistoryMonthly :py SplitGhistoryMonthly(<q-args>).execute()
command! -nargs=* TaskWikiHistoryAnnual :py SplitHistoryAnnual(<q-args>).execute()
command! -nargs=* TaskWikiHistoryMonthly :py SplitHistoryMonthly(<q-args>).execute()
command! -nargs=* TaskWikiStats :py SplitStats(<q-args>).execute()
command! -nargs=* TaskWikiTags :py SplitTags(<q-args>).execute()

" Commands that operate on tasks in the buffer
command! -range TaskWikiInfo :<line1>,<line2>py SelectedTasks().info()
command! -range TaskWikiEdit :<line1>,<line2>py SelectedTasks().edit()
command! -range TaskWikiLink :<line1>,<line2>py SelectedTasks().link()
command! -range TaskWikiGrid :<line1>,<line2>py SelectedTasks().grid()
command! -range TaskWikiDelete :<line1>,<line2>py SelectedTasks().delete()
command! -range TaskWikiStart :<line1>,<line2>py SelectedTasks().start()
command! -range TaskWikiStop :<line1>,<line2>py SelectedTasks().stop()
command! -range TaskWikiDone :<line1>,<line2>py SelectedTasks().done()
command! -range -nargs=* TaskWikiSort :<line1>,<line2>py SelectedTasks().sort(<q-args>)
command! -range -nargs=* TaskWikiMod :<line1>,<line2>py SelectedTasks().modify(<q-args>)
command! -range -nargs=* TaskWikiAnnotate :<line1>,<line2>py SelectedTasks().annotate(<q-args>)

" Interactive commands
command! -range TaskWikiChooseProject :<line1>,<line2>py ChooseSplitProjects("global").execute()
command! -range TaskWikiChooseTag :<line1>,<line2>py ChooseSplitTags("global").execute()

" Meta commands
command! TaskWikiInspect :py Meta().inspect_viewport()

" Disable <CR> as VimwikiFollowLink
if !hasmapto('<Plug>VimwikiFollowLink')
  nmap <Plug>NoVimwikiFollowLink <Plug>VimwikiFollowLink
endif

nmap <silent><buffer> <CR> :py Mappings.task_info_or_vimwiki_follow_link()<CR>

" Leader-related mappings. Mostly <Leader>t + <first letter of the action>
nmap <silent><buffer> <Leader>ta :TaskWikiAnnotate<CR>
nmap <silent><buffer> <Leader>tbd :TaskWikiBurndownDaily<CR>
nmap <silent><buffer> <Leader>tbw :TaskWikiBurndownWeekly<CR>
nmap <silent><buffer> <Leader>tbm :TaskWikiBurndownMonthly<CR>
nmap <silent><buffer> <Leader>tcp :TaskWikiChooseProject<CR>
nmap <silent><buffer> <Leader>tct :TaskWikiChooseTag<CR>
nmap <silent><buffer> <Leader>tC :TaskWikiCalendar<CR>
nmap <silent><buffer> <Leader>td :TaskWikiDone<CR>
nmap <silent><buffer> <Leader>tD :TaskWikiDelete<CR>
nmap <silent><buffer> <Leader>te :TaskWikiEdit<CR>
nmap <silent><buffer> <Leader>tg :TaskWikiGrid<CR>
nmap <silent><buffer> <Leader>tGm :TaskWikiGhistoryMonthly<CR>
nmap <silent><buffer> <Leader>tGa :TaskWikiGhistoryAnnual<CR>
nmap <silent><buffer> <Leader>thm :TaskWikiHistoryMonthly<CR>
nmap <silent><buffer> <Leader>tha :TaskWikiHistoryAnnual<CR>
nmap <silent><buffer> <Leader>ti :TaskWikiInfo<CR>
nmap <silent><buffer> <Leader>tl :TaskWikiLink<CR>
nmap <silent><buffer> <Leader>tm :TaskWikiMod<CR>
nmap <silent><buffer> <Leader>tp :TaskWikiProjects<CR>
nmap <silent><buffer> <Leader>ts :TaskWikiProjectsSummary<CR>
nmap <silent><buffer> <Leader>tS :TaskWikiStats<CR>
nmap <silent><buffer> <Leader>tt :TaskWikiTags<CR>
nmap <silent><buffer> <Leader>t+ :TaskWikiStart<CR>
nmap <silent><buffer> <Leader>t- :TaskWikiStop<CR>

" Mappings for visual mode.
vmap <silent><buffer> <Leader>ta :TaskWikiAnnotate<CR>
vmap <silent><buffer> <Leader>tcp :TaskWikiChooseProject<CR>
vmap <silent><buffer> <Leader>tct :TaskWikiChooseTag<CR>
vmap <silent><buffer> <Leader>td :TaskWikiDone<CR>
vmap <silent><buffer> <Leader>tD :TaskWikiDelete<CR>
vmap <silent><buffer> <Leader>te :TaskWikiEdit<CR>
vmap <silent><buffer> <Leader>tg :TaskWikiGrid<CR>
vmap <silent><buffer> <Leader>ti :TaskWikiInfo<CR>
vmap <silent><buffer> <Leader>tl :TaskWikiLink<CR>
vmap <silent><buffer> <Leader>tm :TaskWikiMod<CR>
vmap <silent><buffer> <Leader>t+ :TaskWikiStart<CR>
vmap <silent><buffer> <Leader>t- :TaskWikiStop<CR>
