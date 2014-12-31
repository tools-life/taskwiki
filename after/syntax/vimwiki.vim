let s:conceal = exists("+conceallevel") ? ' conceal': ''
execute 'syn match VimwikiTaskUuid containedin=VimwikiCheckBoxDone /\v#[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/'.s:conceal
hi link VimwikiTaskUuid Comment
set conceallevel=3
set concealcursor=nc
