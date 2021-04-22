" Disable taskwiki if taskwiki_disable variable set
if exists("g:taskwiki_disable")
  finish
endif

" Detect if conceal feature is available
let s:conceal = exists("+conceallevel") ? ' conceal': ''

syntax match TaskWikiTask /\s*\* \[.\]\s.*$/ contains=@TaskWikiTaskContains
syntax cluster TaskWikiTaskContains
       \ contains=VimwikiListTodo,
                \ VimwikiTag,
                \ VimwikiEmoticons,
                \ VimwikiTodo,
                \ VimwikiBoldT,
                \ VimwikiItalicT,
                \ VimwikiBoldItalicT,
                \ VimwikiItalicBoldT,
                \ VimwikiDelTextT,
                \ VimwikiSuperScriptT,
                \ VimwikiSubScriptT,
                \ VimwikiCodeT,
                \ VimwikiEqInT,
                \ VimwikiLink,
                \ VimwikiNoExistsLink,
                \ VimwikiNoExistsLinkT,
                \ VimwikiWikiLink,
                \ VimwikiWikiLinkT,
                \ @Spell

" Conceal the UUID
execute 'syn match TaskWikiTaskUuid containedin=TaskWikiTask /\v#([A-Z]:)?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/'.s:conceal
execute 'syn match TaskWikiTaskUuid containedin=TaskWikiTask /\v#([A-Z]:)?[0-9a-fA-F]{8}$/'.s:conceal
highlight link TaskWikiTaskUuid Comment

" Conceal header definitions
for s:i in range(1,6)
  execute 'syn match TaskWikiHeaderDef containedin=VimwikiHeader'.s:i.' contained /|[^=]*/'.s:conceal
endfor

" Define active and deleted task regions
" Will be colored dynamically by Meta().source_tw_colors()
syntax match TaskWikiTaskActive containedin=TaskWikiTask contained contains=@TaskWikiTaskContains /\s*\*\s\[S\]\s[^#]*/
syntax match TaskWikiTaskCompleted containedin=TaskWikiTask contained contains=@TaskWikiTaskContains /\s*\*\s\[X\]\s[^#]*/
syntax match TaskWikiTaskDeleted containedin=TaskWikiTask contained contains=@TaskWikiTaskContains /\s*\*\s*\[D\]\s[^#]*/
syntax match TaskWikiTaskRecurring containedin=TaskWikiTask contained contains=@TaskWikiTaskContains /\s*\*\s\[R\]\s[^#]*/
syntax match TaskWikiTaskWaiting containedin=TaskWikiTask contained contains=@TaskWikiTaskContains /\s*\*\s\[W\]\s[^#]*/
syntax match TaskWikiTaskPriority contained /\( \)\@<=\(!\|!!\|!!!\)\( \)\@=/
syntax cluster TaskWikiTaskContains add=TaskWikiTaskPriority

" Set concealed parts as really concealed in normal mode, and with cursor over
" (unless disabled by user)
if !exists('g:taskwiki_disable_concealcursor')
  setlocal conceallevel=3
  setlocal concealcursor=nc
endif
