import fdb
import metadata
from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)

#DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'
DB_PATH = 'localhost:E:/CloudMail.Ru/db/TIMETABLE.FDB'

class queryBuilder:
    query = ''

    def __init__(self, table, meta, searchCol, searchRequest, operator):
        self.createQuery(table, meta)
        self.joinTable(table, meta)
        self.addSearchRequest(table, searchCol, searchRequest, operator)

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

    def addSearchRequest(self, table, searchCol, searchRequest, operator):
        if searchRequest != '':
            self.query += ' where %s.%s %s \'%s\''
            if isinstance(searchCol, metadata.RefField):
                self.query = self.query % (searchCol.referenceTable.tableName, searchCol.referenceCol.colName, operator,
                                           searchRequest)
            else:
                self.query = self.query % (table.tableName, searchCol.colName, operator, searchRequest)
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
        tables = [
            'AUDIENCES',
            'GROUPS',
            'LESSONS',
            'LESSON_TYPES',
            'SCHED_ITEMS',
            'SUBJECTS',
            'SUBJECT_GROUP',
            'SUBJECT_TEACHER',
            'TEACHERS',
            'WEEKDAYS'
        ]
        operators = [
            '=',
            '>',
            '>=',
            '<',
            '<='
        ]
        selected_table = request.args.get('t', '')
        selected_column = request.args.get('c', '')
        selected_operator = request.args.get('op', '')
        
        #######ERRORS /\ check for in dict
        search_request = ''
        rows = []
        meta = []
        if selected_table in tables:
            selected_table = getattr(metadata,selected_table)
            if selected_column in selected_table.__dict__:
                selected_column = getattr(selected_table, selected_column)
                if selected_column.type == 'int':
                    search_request = request.args.get('s', '', type=int)
                else:
                    search_request = request.args.get('s', '')
            for field in selected_table.__dict__:
                attr = getattr(selected_table,field)
                if isinstance(attr,metadata.BaseField) or isinstance(attr, metadata.RefField):
                    meta.append(getattr(selected_table,field))
            query = queryBuilder(selected_table,meta, selected_column, str(search_request).replace('\'', '\'\''),
                                 selected_operator).query
            print('---------QUERY----------')
            print(query)
            print('---------QUERY----------')
            cur.execute(query)
            rows = cur.fetchall()
        return render_template("index.html",
            tables = tables,
            rows = rows,
            selected_table = selected_table,
            selected_column = selected_column,
            selected_operator = selected_operator,
            search_request = search_request,
            meta = meta,
            operators = operators)
    finally:
        con.close()
#app.run(debug=True)