// Verbose
//Database = require('arangojs').Database;
//db = new Database('http://127.0.0.1:8529');

// Concise
db = require('arangojs')('http://127.0.0.1:8529');
aqlQuery = require('arangojs').aqlQuery;
db.useDatabase('TDB');
db.useBasicAuth("root", "u@#TmqF1");
const { Pool, Client } = require('pg');

const connectionString = 'postgres://postgres:p73xRmtvMax@127.0.0.1:5433/hinyango';

const pool = new Pool({
  connectionString: connectionString,
});

var querystr = `
SELECT  a.id, 
    nickname, 
    to_char(start_date, 'DD/MM/YYYY') as start_date, 
    to_char(end_date,'DD/MM/YYYY') as end_date, 
    case when confirmed_id = 1 then 'Yes' else 'No' End as confirmed, 
    groupkey_id, 
    c.project_name,
    a.projectmap_id,
    b.impact_type, 
    ampp, 
    resources
  FROM dandywidgets.ccprojects_projectchange a 
  left join dandywidgets.ccprojects_impacttype b on a.impact_type_id = b.id
  left join dandywidgets.ccprojects_projectstructure c on a.projectmap_id = c.id
  where a.type_required = 'Change' and inactive_date is null
  order by id
`;

pool.query(querystr, (err, res) => {
  console.log(err, res)
  pool.end()
});



db.query(aqlQuery`
let cdata = (for bu in dandywidgets_businessUnit
FILTER bu.change_data != null
RETURN {bu_label: bu.bu_unit_label,
        bu_name:bu.name,
        bu_id:bu._key,
        resources:bu.resource_count,
        bu_fid:bu._id,
        bu_change_pk:(
            for cd in bu.change_data
FILTER cd.change_pk == '165'

RETURN {change_pk:cd.change_pk,project_id:cd.project_id})})
for itm in cdata
FILTER length(itm.bu_change_pk) > 0
return {bu_label:itm.bu_label,resources:itm.resources,bu_id:itm.bu_id,change_pk:itm.bu_change_pk[0]['change_pk'],project_id:itm.bu_change_pk[0]['project_id']}
    `).then(
  cursor => cursor.all()
).then(
  keys => console.log(keys),
  err => console.error('Failed to insert:', err)
);
