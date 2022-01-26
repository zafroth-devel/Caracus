/**
  SELECT type_required,groupkey_id,impact_type_id
  FROM dandywidgets.ccprojects_projectchange
  where type_required = 'Project'
  order by type_required,groupkey_id,impact_type_id
  **/
update dandywidgets.ccprojects_projectchange a
set impact_type_id = b.impact_type_id
from 
 (with blah as (
  select
    *,
    row_number() over (partition by type_required,groupkey_id) as row_number
  from dandywidgets.ccprojects_projectchange
  where type_required = 'Project'
)
select type_required,groupkey_id,impact_type_id,row_number
  from blah
  where type_required = 'Project' and row_number = 1
   order by type_required,groupkey_id,row_number) b
   where a.groupkey_id = b.groupkey_id