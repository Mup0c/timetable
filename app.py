from math import ceil
from flask import Flask
from flask import render_template
from flask import abort
from werkzeug.urls import url_encode
from conflicts import *

app = Flask(__name__)

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
    selected_table = getattr(metadata, selected_table)
    row = request.args.get('r', -1, type=int)
    col = request.args.get('c', -1, type=int)
    meta = getMeta(selected_table)
    meta.pop(0) #Удалить поле ID, т.к. его нельзя изменять пользователю
    query = QueryBuilder.getRowToModify(QueryBuilder(), selected_table, selected_id, meta)
    cur.execute(query)
    rows = cur.fetchall()
    if rows == []:
        abort(404)
    newValues = getNewValues(meta)
    anyValues = False
    for i in range(len(newValues)):
        if newValues[i] != None:
            anyValues = True
        else:
            newValues[i] = rows[0][i]
    if anyValues:
        query = QueryBuilder.getUpdate(QueryBuilder(), selected_table, selected_id, meta)
        try:
            cur.execute(query, newValues)
            cur.transaction.commit()
            updateConflicts()
        except:
            return 'Ошибка: не существует введенного ID в зависимой таблице'
    return render_template("modify.html",
        selected_id = selected_id,
        selected_table = selected_table,
        row = newValues,
        olap_row=row,
        olap_col=col,
        meta = meta
    )

@app.route("/insert/<string:selected_table>/")
def insertPage(selected_table):
    if not selected_table in tables:
        abort(404)
    selected_table = getattr(metadata, selected_table)
    meta = getMeta(selected_table)
    row = request.args.get('r', -1, type=int)
    col = request.args.get('c', -1, type=int)
    row_val = request.args.get('rval', None, type=int)
    col_val = request.args.get('cval', None, type=int)
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
            updateConflicts()
        except:
            return 'Ошибка: не существует введенного ID в зависимой таблице'
    return render_template("insert.html",
                           selected_table = selected_table,
                           meta = meta,
                           olap_row = row,
                           olap_col = col,
                           row_val = row_val,
                           col_val = col_val
                           )

@app.route("/analytics/")
def analyticsPage():
    table = metadata.SCHED_ITEMS
    meta = getMeta(table)
    viewedNames = [col.viewedName for col in meta]
    search = Search(table)
    idToDelete = request.args.get('delID', -1, type=int)
    if idToDelete != -1:
        deleteRow(table.tableName, idToDelete)
    selected_col = request.args.get('col', 1, type=int) #default - Пара
    selected_row = request.args.get('row', 7, type=int) #default - День недели
    showNames = request.args.get('showNames', 1, type=int)
    wasSubmitted = request.args.get('wasSubmitted', 0, type=int)
    showed_cols = [i for i in range(len(viewedNames)) if ((request.args.get(str(i), 1, type=int)) if wasSubmitted else
        (i != selected_row and i != selected_col and i != 0))] #не показывать проекции и ID по умолчанию
    if not (selected_col in range(len(viewedNames)) and selected_row in range(len(viewedNames))):
        selected_col = 1 #Пара
        selected_row = 7 #День недели

    cur.execute(QueryBuilder.getTableRows(QueryBuilder(),meta[selected_row].referenceTable if not selected_row == 0 else table))
    rows = cur.fetchall()
    if not selected_row == 0: rows.append((None,None))
    cur.execute(QueryBuilder.getTableRows(QueryBuilder(),meta[selected_col].referenceTable if not selected_col == 0 else table))
    cols = cur.fetchall()
    if not selected_col == 0: cols.append((None,None))
    viewed_table = dict.fromkeys([(col[1],col[0]) if not selected_col == 0 else (col[0],col[0]) for col in cols])
    for col in viewed_table:
        viewed_table[col] = dict.fromkeys([(row[1],row[0]) if not selected_row == 0 else (row[0],row[0]) for row in rows])

    query = QueryBuilder.getAnalyticsView(QueryBuilder(), table, meta, search)
    cur.execute(query, search.getRequests())
    rows = cur.fetchall()
    rows_name = []
    rows_id = []
    for row in rows:
        rows_name.append([])
        rows_id.append([row[0]])
        for i in range(len(row)):
            rows_name[-1].append(row[i]) if i == 0 or i % 2 else rows_id[-1].append(row[i])
    for i in range(len(rows_name)):
        for j in range(len(rows_name[i])):
            rows_name[i][j] = (rows_name[i][j], rows_id[i][j])

    rows = rows_name
    for row in rows:
        if viewed_table[row[selected_col]][row[selected_row]] == None:
            viewed_table[row[selected_col]][row[selected_row]] = [row]
        else:
            viewed_table[row[selected_col]][row[selected_row]].append(row)
    query = QueryBuilder.getConflictingIDs(QueryBuilder())
    cur.execute(query)
    conflictingIDs = cur.fetchall()
    conflictingIDs = [item[0] for item in conflictingIDs]
    return render_template("analytics.html",
                           operators=operators,
                           viewed_table = viewed_table,
                           search=search,
                           selected_col = selected_col,
                           selected_row = selected_row,
                           showed_cols = showed_cols,
                           meta = meta,
                           showNames = showNames,
                           viewedNames = viewedNames,
                           wasSubmitted = wasSubmitted,
                           conflictingIDs=conflictingIDs,
                           idToDelete=-1
                           )

def deleteRow(table, id):
    if not table in tables:
        return 0
    cur.execute('delete from %s where ID = %d' % (table, id))
    cur.transaction.commit()
    updateConflicts()
    return 0

@app.route("/conflicts/")
@app.route("/conflicts/<int:type_id>")
def conflict(type_id = 0):
    if not type_id in range(3):
        abort(404)
    table = metadata.SCHED_ITEMS
    meta = getMeta(table)
    viewedNames = [col.viewedName for col in meta]
    idToDelete = request.args.get('delID', -1, type=int)
    if idToDelete != -1:
        deleteRow(table.tableName, idToDelete)
    query = QueryBuilder.getConflict(QueryBuilder(), table, meta, type_id)
    cur.execute(query)
    rows = cur.fetchall()
    conflicts_by_groups = [[]]
    last_group_id = -1
    for conflict in rows:
        if conflict == rows[0]:
            last_group_id = conflict[0]
        if conflict[0] != last_group_id:
            conflicts_by_groups.append([])
        conflicts_by_groups[-1].append(conflict[1:])
        last_group_id = conflict[0]
    return render_template("conflicts_page.html",
                           rows_list=conflicts_by_groups,
                           meta=meta,
                           viewedNames=viewedNames,
                           idToDelete=-1,
                           conflicts=conflicts_meta
                           )


app.run(debug=True)