import fdb
import metadata
from metadata import *
from flask import Flask
from flask import request
from flask import render_template
from werkzeug.urls import url_encode

app = Flask(__name__)

#DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'
DB_PATH = 'localhost:E:/CloudMail.Ru/db/TIMETABLE.FDB'




"""
добавить тип int str ordering и делать если ордеринг еще один жоин, сорт тоже делать по нему
"""






class Search:

    def __init__(self, table):
        self.requests = []
        self.columns = []
        self.operators = []
        self.count = 0
        self.count += getUnsigned(request.args.get('cnt', 1, type=int))
        for i in range(self.count):
            temp_col = request.args.get('c' + str(i), '')
            if temp_col in table.__dict__:
                self.columns.append(getattr(table, temp_col))
                if self.columns[-1].type == 'int':
                    self.requests.append(request.args.get('s' + str(i), '', type=int))
                else:
                    self.requests.append(str(request.args.get('s' + str(i), '')).replace('\'', '\'\''))
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

    def __init__(self, table, meta, search):
        self.createQuery(table, meta)
        self.joinTable(table, meta)
        self.addSearchRequest(table, search)
        self.addSort(table, meta)

    def createQuery(self, table, meta):
        self.query = 'select %s from ' + table.tableName
        return self.query

    def joinTable(self, table, meta):
        colsToSelect = []
        for field in meta:
            if isinstance(field, metadata.RefField):
                self.query += ' left join ' + field.referenceTable.tableName + ' on '  + \
                              table.tableName + '.' + field.colName +  ' = ' + \
                              field.referenceTable.tableName + '.' + field.referenceTable.id.colName + '\n'
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
                                               search.operators[i], search.requests[i])
                elif isinstance(search.columns[i], metadata.BaseField):
                    request[-1] = request[-1] % (table.tableName, search.columns[i].colName,
                                               search.operators[i], search.requests[i])
                else:
                    request.pop()
        if request != []:
            self.query += ' where ' + ' and '.join(request)
        return self.query

    def addSort(self, table, meta):
        col = request.args.get('srt','')
        if col in table.__dict__:
            col = getattr(table, col)
            if isinstance(col, metadata.RefField):
                self.query += ' order by %s.%s' % (col.referenceTable.tableName, col.referenceCol.colName)
            elif isinstance(col, metadata.BaseField):
                self.query += ' order by %s.%s' % (table.tableName, col.colName)
        return self.query

def getUnsigned(num):
    return int((abs(num) + num) / 2)

@app.template_global()
def changeArg(arg, val):
    print('---------changeArg----------')
    print(arg)
    print(val)
    print('---------changeArg----------')
    args = request.args.copy()
    args[arg] = val
    return '{}?{}'.format(request.path, url_encode(args))


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

        selected_table = request.args.get('t', '')
        rows = []
        meta = []
        search = Search(getattr(metadata, tables[0]))
        if selected_table in tables:
            selected_table = getattr(metadata,selected_table)
            search = Search(selected_table)
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
            query = QueryBuilder(selected_table, meta, search).query
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
            meta = meta
            )
    finally:
        con.close()
#app.run(debug=True)