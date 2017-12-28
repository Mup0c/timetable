import fdb
from math import ceil
from flask import Flask
from flask import render_template
from flask import abort
from werkzeug.urls import url_encode
from query import *

app = Flask(__name__)

DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'
#DB_PATH = 'localhost:E:/CloudMail.Ru/db/TIMETABLE.FDB'

def getMeta(table):
    meta = []
    for field in table.__dict__:
        attr = getattr(table, field)
        if isinstance(attr, metadata.BaseField) or isinstance(attr, metadata.RefField):
            meta.append(getattr(table, field))
    return meta

class Paging:

    def __init__(self, cur):
        self.cur = cur

    def nextInit(self, query, params):
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

@app.route("/")
def home():
    con = fdb.connect(
    dsn=DB_PATH,
    user='SYSDBA',
    password='masterkey',
    charset='UTF-8'
    )
    cur = con.cursor()
    sortCol = request.args.get('srt', '')
    selected_table = request.args.get('t', '')
    if selected_table in tables:
        selected_table = getattr(metadata,selected_table)
    else:
        selected_table = getattr(metadata, tables[0])
    meta = getMeta(selected_table)
    search = Search(selected_table)
    paging = Paging(cur)
    idToDelete = request.args.get('delID', -1, type=int)
    if idToDelete != -1:
        deleteRow(selected_table.tableName, idToDelete)
    query = QueryBuilder.getTableView(QueryBuilder(),selected_table, meta, search, paging, sortCol)
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
        sortCol = sortCol,
        idToDelete = -1
        )

def getNewValues(meta):
    return [request.args.get(field.colName, None,
        type=(int if (field.type != 'str' and field.type != 'ref_ord') else None))
            for field in meta]

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
    meta.pop(0) #Удалить поле ID, т.к. его нельзя изменять пользователю
    newValues = getNewValues(meta)
    anyValues = False
    for value in newValues:
        if value != None: anyValues = True
    if anyValues:
        query = QueryBuilder.getUpdate(QueryBuilder(), selected_table, selected_id, meta)
        try:
            cur.execute(query, newValues)
            cur.transaction.commit()
        except:
            return 'Ошибка: не существует введенного ID в зависимой таблице'
    query = QueryBuilder.getRowToModify(QueryBuilder(), selected_table, selected_id, meta)
    cur.execute(query)
    rows = cur.fetchall()
    if rows == []:
        abort(404)
    return render_template("modify.html",
        selected_id = selected_id,
        selected_table = selected_table,
        row = rows[0],
        meta = meta
    )

@app.route("/insert/<string:selected_table>/")
def insertPage(selected_table):
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
    meta.pop(0) #Удалить поле ID, т.к. его нельзя вводить пользователю
    newValues = getNewValues(meta)
    anyValues = False
    for value in newValues:
        if value != None: anyValues = True
    if anyValues:
        query = QueryBuilder.getInsert(QueryBuilder(), selected_table, meta)
        try:
            cur.execute(query, newValues)
            cur.transaction.commit()
        except:
            return 'Ошибка: не существует введенного ID в зависимой таблице'
    return render_template("insert.html",
                           selected_table = selected_table,
                           meta = meta
                           )

@app.route("/analytics/")
def analyticsPage():#вынести в перед app.route:   #повесить заполнение галочек на кнопу (если кнопка сабмит нажата хоть раз, то не ставить дефолт галочки
    con = fdb.connect(
        dsn=DB_PATH,
        user='SYSDBA',
        password='masterkey',
        charset='UTF-8'
    )
    cur = con.cursor()
    table = getattr(metadata, tables[4])
    meta = getMeta(table) #table.getmeta
    viewedNames = [col.viewedName for col in meta]
    search = Search(table)
    selected_col = request.args.get('col', '')
    selected_row = request.args.get('row', '')
    showNames = request.args.get('showNames', 1, type=int)
    showed_cols = []
    for name in viewedNames: #comprehention, параметры сделать английскими
        if request.args.get(name, 1, type=int): showed_cols.append(viewedNames.index(name)) #плохо брать индекс, делать нормальный итератор (инт) (или нет)
    if not (selected_col in viewedNames and selected_row in viewedNames):
        selected_col = 1   #
        selected_row = 1
    else:
        selected_col = viewedNames.index(selected_col) ##
        selected_row = viewedNames.index(selected_row)
    query = QueryBuilder.getAnalyticsView(QueryBuilder(), table, meta, search)
    cur.execute(query, search.getRequests())
    rows = cur.fetchall()
    rows = [list(row) for row in rows]
    viewed_table = dict.fromkeys([row[selected_col] for row in rows])
    #viewed_table = dict.fromkeys(list(row)[selected_col] for row in rows)
    for col in viewed_table:
        viewed_table[col] = dict.fromkeys([col[selected_row] for col in rows])
    for row in rows:
        if viewed_table[row[selected_col]][row[selected_row]] == None: #viewed table в переменную ??
            viewed_table[row[selected_col]][row[selected_row]] = [row]
        else:
            viewed_table[row[selected_col]][row[selected_row]].append(row)
    return render_template("analytics.html",
        operators=operators,
        viewed_table = viewed_table,
        search=search,
        selected_col = selected_col,
        selected_row = selected_row,
        showed_cols = showed_cols,
        meta = meta,
        showNames = showNames,
        viewedNames = viewedNames
    )

def deleteRow(table, id):
    if not table in tables:
        return 0
    con = fdb.connect(
        dsn=DB_PATH,
        user='SYSDBA',
        password='masterkey',
        charset='UTF-8'
    )
    cur = con.cursor()
    cur.execute('delete from %s where ID = %d' % (table, id))
    cur.transaction.commit()
    return 0


app.run(debug=True)