import fdb
from flask import Flask
from flask import request
from flask import render_template
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

        cur.execute(''' select RDB$RELATION_NAME from RDB$RELATIONS
                        where (RDB$SYSTEM_FLAG = 0) AND (RDB$RELATION_TYPE = 0)
                        order by RDB$RELATION_NAME''')
        tables = []
        for row in cur.fetchall():
            str_name = str(row[0]).strip()
            tables.append(str_name)

        selected_table = request.args.get('t', '')
        if selected_table in tables:
            cur.execute('select * from ' + str(selected_table))
        return render_template("index.html",
        tables = tables, result = cur.fetchall(), selected_table = selected_table)
    finally:
        con.close()


