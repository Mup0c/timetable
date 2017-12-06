import fdb
import metadata
from math import ceil
from metadata import *
from flask import Flask
from flask import request
from flask import render_template
from werkzeug.urls import url_encode

app = Flask(__name__)

#DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'
DB_PATH = 'localhost:E:/CloudMail.Ru/db/TIMETABLE.FDB'

class Paging:

    def __init__(self, cur):
        self.cur = cur

    def nextInit(self, query):
        print(query)
        self.cur.execute(query)
        self.rowsNum = int(self.cur.fetchall()[0][0])
        self.OnPage = makeNat(request.args.get('onpage', 5, type=int))
        if self.OnPage > 10000: self.OnPage = 10000
        self.pagesNum = int(ceil(self.rowsNum / self.OnPage))
        self.page = request.args.get('page', 0, type=int)
        if not self.page in range(self.pagesNum):
            self.page = 0

class Search:

    def __init__(self, table):
        self.requests = []
        self.columns = []
        self.operators = []
        self.count = 0
        self.count += makeNat(request.args.get('cnt', 1, type=int))
        if self.count > 14: self.count = 14
        for i in range(self.count):
            temp_col = request.args.get('c' + str(i), '')
            if temp_col in table.__dict__:
                self.columns.append(getattr(table, temp_col))
                if self.columns[-1].type == 'int':
                    self.requests.append(request.args.get('s' + str(i), '', type=int))
                else:
                    self.requests.append(request.args.get('s' + str(i), ''))
            else:
                self.columns.append('')
                self.requests.append('')
            temp_op = request.args.get('op' + str(i), '')
            if temp_op in operators:
                self.operators.append(temp_op)
            else:
                self.operators.append(operators[0])

class QueryBuilder:
    query = ''

    def __init__(self, table, meta, search, paging):
        self.createQuery(table, meta)
        self.joinTable(table, meta)
        self.addSearchRequest(table, search)
        self.addSort(table, meta)
        self.addPage(paging)

    def createQuery(self, table, meta):
        self.query = 'select %s from ' + table.tableName
        self.countQuery = 'select count(*) from ' + table.tableName
        return self.query

    def joinTable(self, table, meta):
        colsToSelect = []
        for field in meta:
            if isinstance(field, metadata.RefField):
                temp = ' left join ' + field.referenceTable.tableName + ' on '  + \
                              table.tableName + '.' + field.colName +  ' = ' + \
                              field.referenceTable.tableName + '.' + field.referenceTable.id.colName + '\n'
                self.query += temp
                self.countQuery += temp
                colsToSelect.append(field.referenceTable.tableName + '.' + field.referenceCol.colName)
            else:
                colsToSelect.append(table.tableName + '.' + field.colName)
        self.query = self.query % ','.join(colsToSelect)
        return self.query

    def addSearchRequest(self, table, search):
        request = []
        for i in range(search.count):
            if search.requests[i] != '':
                request.append('%s.%s %s \'%s\'')
                if isinstance(search.columns[i], metadata.RefField):
                    request[-1] = request[-1] % (search.columns[i].referenceTable.tableName,
                                               search.columns[i].referenceCol.colName,
                                               search.operators[i], str(search.requests[i]).replace('\'', '\'\''))
                elif isinstance(search.columns[i], metadata.BaseField):
                    request[-1] = request[-1] % (table.tableName, search.columns[i].colName,
                                               search.operators[i], str(search.requests[i]).replace('\'', '\'\''))
                else:
                    request.pop()
        if request != []:
            temp = ' where ' + ' and '.join(request)
            self.countQuery += temp
            self.query += temp
        return self.query

    def addSort(self, table, meta):
        col = request.args.get('srt','')
        if col in table.__dict__:
            col = getattr(table, col)
        else:
            col = meta[0]
        if col in meta:
            if isinstance(col, metadata.RefField):
                tname = col.referenceTable.tableName
                cname = col.referenceCol.colName
                ctype = col.referenceCol.type
            else:
                tname = table.tableName
                cname = col.colName
                ctype = col.type
            self.query += ' order by %s.%s'
            if ctype == "reford":
                self.query += ', %s.%s'
                self.query = self.query % (tname, "order_number", tname, cname)
            else:
                self.query = self.query % (tname, cname)
        return self.query

    def addPage(self, paging):
        paging.nextInit(self.countQuery)
        self.query += ' offset %d rows fetch next %d rows only'
        self.query = self.query % (paging.OnPage*paging.page, paging.OnPage)
        return self.query



def makeNat(num):
    a = int((abs(num) + num) / 2)
    if a == 0: a = 1;
    return a

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
def hello():
    con = fdb.connect(
    dsn=DB_PATH,
    user='SYSDBA',
    password='masterkey',
    charset='UTF-8'
    )

    try:
        cur = con.cursor()
        meta = []
        selected_table = request.args.get('t', '')
        if selected_table in tables:
            selected_table = getattr(metadata,selected_table)
        else:
            selected_table = getattr(metadata, tables[0])
        search = Search(selected_table)
        paging = Paging(cur)
        print('---------search----------')
        print(search.count)
        print(search.requests)
        print(search.columns)
        print(search.operators)
        print('---------search----------')
        for field in selected_table.__dict__:
            attr = getattr(selected_table,field)
            if isinstance(attr,metadata.BaseField) or isinstance(attr, metadata.RefField):
                meta.append(getattr(selected_table,field))
        query = QueryBuilder(selected_table, meta, search, paging).query
        print('---------QUERY----------')
        print(query)
        print('---------QUERY----------')
        cur.execute(query)
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
    finally:
        con.close()

@app.route("/modify/")
def modif():
    pass
#app.run(debug=True)