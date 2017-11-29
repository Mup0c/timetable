import fdb
import metadata
from metadata import *
from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)

#DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'
DB_PATH = 'localhost:E:/CloudMail.Ru/db/TIMETABLE.FDB'

class Search:

    def __init__(self, table):
        self.requests = []
        self.columns = []
        self.operators = []
        self.count = 2
        try:
            self.count += int(request.args.get('cnt', '', type=int)) ###########
        except:
            pass
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
        '''
        selected_column = request.args.get('c', '')
        selected_operator = request.args.get('op', '')
        search_request = ''
        '''
        rows = []
        meta = []
        search = Search(getattr(metadata, tables[0])) #check
        if selected_table in tables:
            selected_table = getattr(metadata,selected_table)
            search = Search(selected_table)
            print('---------search----------')
            print(search.count)
            print(search.requests)
            print(search.columns)
            print(search.operators)
            print('---------search----------')
            '''
            if selected_column in selected_table.__dict__:
                selected_column = getattr(selected_table, selected_column)
                if selected_column.type == 'int':
                    search_request = request.args.get('s', '', type=int)
                else:
                    search_request = request.args.get('s', '')
            '''
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