import fdb
from math import ceil
from flask import Flask
from flask import render_template
from flask import abort
from werkzeug.urls import url_encode
from query import *

app = Flask(__name__)

#DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'
DB_PATH = 'localhost:E:/CloudMail.Ru/db/TIMETABLE.FDB'



class Paging:

    def __init__(self, cur):
        self.cur = cur

    def nextInit(self, query, params):
        print('----------ROWS QUERY---------------')
        print(query)
        print(params)
        print('----------ROWS QUERY---------------')
        self.cur.execute(query, params)
        self.rowsNum = int(self.cur.fetchall()[0][0])
        self.onPage = min(10000,max(1,request.args.get('onpage', 5, type=int)))
        self.pagesNum = int(ceil(self.rowsNum / self.onPage))
        self.page = request.args.get('page', 0, type=int)
        if not self.page in range(self.pagesNum):
            self.page = 0

@app.template_global()
def changeArg(arg, val):
    args = request.args.copy()
    args[arg] = val
    return '{}?{}'.format(request.path, url_encode(args))

def getMeta(table):
    meta = []
    for field in table.__dict__:
        attr = getattr(table, field)
        if isinstance(attr, metadata.BaseField) or isinstance(attr, metadata.RefField):
            meta.append(getattr(table, field))
    return meta

@app.route("/")
def home():
    con = fdb.connect(
    dsn=DB_PATH,
    user='SYSDBA',
    password='masterkey',
    charset='UTF-8'
    )
    cur = con.cursor()
    selected_table = request.args.get('t', '')
    if selected_table in tables:
        selected_table = getattr(metadata,selected_table)
    else:
        selected_table = getattr(metadata, tables[0])
    meta = getMeta(selected_table)
    search = Search(selected_table)
    paging = Paging(cur)
    query = QueryBuilder.getTableView(QueryBuilder(),selected_table, meta, search, paging)
    print('-----------------------QUERY-----------------------')
    print(query)
    print(search.getRequests())
    print('-----------------------QUERY-----------------------')
    cur.execute(query, search.getRequests())
    rows = cur.fetchall()
    return render_template("index.html",
        tables = tables,
        operators = operators,
        selected_table = selected_table,
        rows = rows,
        search = search,
        meta = meta,
        paging = paging,
        )

@app.route("/modify/<string:selected_table>/<int:selected_id>/")
def modifyPage(selected_table, selected_id):
    if not selected_table in tables:
        abort(404)
    con = fdb.connect(
        dsn=DB_PATH,
        user='SYSDBA',
        password='masterkey',
        charset='UTF-8'
    )
    cur = con.cursor()
    selected_table = getattr(metadata, selected_table)
    meta = getMeta(selected_table)
    query = QueryBuilder.getRowToModify(QueryBuilder(), selected_table, selected_id, meta)
    cur.execute(query)
    rows = cur.fetchall()
    return render_template("modify.html",
                           selected_id = selected_id,
                           selected_table = selected_table,
                           row = rows[0],
                           meta = meta
                           )

@app.template_global()
def modify(table, id, meta):
    print(table)
    print(meta)
    print(id)

app.run(debug=True)