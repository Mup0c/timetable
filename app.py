import fdb
from math import ceil
from flask import Flask
from flask import render_template
from werkzeug.urls import url_encode
from query import *

app = Flask(__name__)

#DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'
DB_PATH = 'localhost:E:/CloudMail.Ru/db/TIMETABLE.FDB'



class Paging:

    def __init__(self, cur):
        self.cur = cur

    def nextInit(self, query, params):
        self.cur.execute(query, params)
        self.rowsNum = int(self.cur.fetchall()[0][0])
        self.OnPage = min(10000,max(1,request.args.get('onpage', 5, type=int)))
        self.pagesNum = int(ceil(self.rowsNum / self.OnPage))
        self.page = request.args.get('page', 0, type=int)
        if not self.page in range(self.pagesNum):
            self.page = 0

@app.template_global()
def changeArg(arg, val):
    args = request.args.copy()
    args[arg] = val
    return '{}?{}'.format(request.path, url_encode(args))

@app.template_global()
def getModifyPageUrl(table, id):
    args = {}
    args['t'] = table
    args['id'] = id
    return '/modify' + '{}?{}'.format(request.path, url_encode(args))


@app.route("/")
def home():
    con = fdb.connect(
    dsn=DB_PATH,
    user='SYSDBA',
    password='masterkey',
    charset='UTF-8'
    )
    cur = con.cursor()
    meta = []
    selected_table = request.args.get('t', '')
    if selected_table in tables:
        selected_table = getattr(metadata,selected_table)
    else:
        selected_table = getattr(metadata, tables[0])
    for field in selected_table.__dict__:
        attr = getattr(selected_table,field)
        if isinstance(attr,metadata.BaseField) or isinstance(attr, metadata.RefField):
            meta.append(getattr(selected_table,field))
    search = Search(selected_table)
    paging = Paging(cur)
    query = QueryBuilder(selected_table, meta, search, paging).query
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

@app.route("/modify/")
def modif():
    return 'memkek'


app.run(debug=True)