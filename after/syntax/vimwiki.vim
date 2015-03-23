syntax match VimwikiCheckBoxActive /\*\s*\[S\]\s.*$/
hi def link VimwikiCheckBoxActive Type

let s:conceal = exists("+conceallevel") ? ' conceal': ''
execute 'syn match VimwikiTaskUuid containedin=VimwikiCheckBoxDone,VimwikiCheckBoxActive /\v#[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/'.s:conceal
hi link VimwikiTaskUuid Comment

setlocal conceallevel=3
setlocal concealcursor=nc
