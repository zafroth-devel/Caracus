from ccutilities.customquery import customsql

var1 = """
SELECT a.id,
       a.type_required, 
       a.nickname, 
       a.start_date, 
       a.end_date, 
       a.propogate, 
       a.answers_id, 
       a.confirmed_id, 
       a.groupkey_id, 
       a.projectmap_id, 
       a.question_id,
       b.name,
       b.description,
       b.aweight as qweight,
       b.question,
       ((select max(rank) from fruity.ccprojects_questiongroup)+1) - b.rank as question_score,
       b.active,
       b.na,
       c.answers,
       c.aweight,
       (d.max_arank+1) - c.arank as answer_score
  from fruity.ccprojects_projectchange a
  left join fruity.ccprojects_questiongroup b on a.question_id = b.id
  left join fruity.ccprojects_answergroup c on a.answers_id = c.id
  left join
  (select a.id,
       b.max_arank
  from fruity.ccprojects_answergroup a 
  left join (
  select question_map_id,max(arank) as max_arank
  from fruity.ccprojects_answergroup 
  group by question_map_id) b on a.question_map_id = b.question_map_id
  order by a.id) d on a.answers_id = d.id
  where c.answers != 'NA' -- All results with an NA answer are removed
        and start_date >= %s
        and end_date   <= %s"""

params = ['2017-09-13','2018-09-14']

geo = customsql(var1,params).qdict()