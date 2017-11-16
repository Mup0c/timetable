import fdb
from flask import Flask
from flask import request
from flask import render_template
import metadata
app = Flask(__name__)
DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'

@app.route("/")
def hello():
    con = fdb.connect(
    dsn=DB_PATH,
    user='SYSDBA',
    password='masterkey',
    charset='UTF8'
    )

    try:
        cur = con.cursor()
        query = '''select RDB$RELATION_NAME from RDB$RELATIONS
                        where (RDB$SYSTEM_FLAG = 0) AND (RDB$RELATION_TYPE = 0)
                        order by RDB$RELATION_NAME'''
        cur.execute(query)
        tables = []
        for row in cur.fetchall():
            str_name = str(row[0]).strip()
            tables.append(str_name)

        selected_table = request.args.get('t', '')
        if selected_table in tables:
            selected_table = getattr(metadata,selected_table)

            table_fields = []
            query = '''select RDB$FIELD_NAME
                          from RDB$RELATION_FIELDS
                          where RDB$SYSTEM_FLAG = 0 and RDB$RELATION_NAME ='%s'
                          order by RDB$FIELD_POSITION'''%selected_table.table
            i = 0
            for field in selected_table.columns:
                table_fields.append(selected_table.columns[field])

            cur.execute('select * from ' + selected_table.table)
        return render_template("index.html",
            tables = tables,
            result = cur.fetchall(),
            selected_table = selected_table,
            table_fields = table_fields)
    finally:
        con.close()