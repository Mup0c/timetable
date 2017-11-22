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

    def __init__(self, table, meta, searchCol, searchRequest):
        self.createQuery(table, meta)
        self.joinTable(table, meta)
        self.addSearchRequest(table, searchCol, searchRequest)

    def createQuery(self, table, meta):
        self.query = 'select %s from ' + table.tableName
        return self.query

    def joinTable(self, table, meta):
        colsToSelect = ','.join(table.tableName + "." + field.colName for field in meta)
        for field in meta:
            if isinstance(field, metadata.RefField):
                self.query += ' left join ' + field.referenceTable.tableName + ' on '  + \
                              table.tableName + '.' + field.colName +  ' = ' + \
                              field.referenceTable.tableName + '.' + field.referenceTable.id.colName + "\n"
                colsToSelect = colsToSelect.replace(table.tableName + "." + field.colName,
                                                    field.referenceTable.tableName + '.' + field.referenceCol.colName, 1)
        self.query = self.query % colsToSelect
        return self.query

    def addSearchRequest(self, table, searchCol, searchRequest):
        if searchRequest != '':
            if isinstance(searchCol, metadata.RefField):
                self.query += ' where ' + searchCol.referenceTable.tableName + '.' + searchCol.referenceCol.colName + ' like \'' + \
                              searchRequest + '\''
            else:
                self.query += ' where ' + table.tableName + '.' + searchCol.colName + ' like \'' + \
                              searchRequest + '\''
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
        selected_table = request.args.get('t', '')
        selected_column = request.args.get('c', '')
        search_request = str(request.args.get('s', '')).replace('\'','')
        rows = []
        meta = []
        if selected_table in tables:
            selected_table = getattr(metadata,selected_table)
            if selected_column in selected_table.__dict__:
                selected_column = getattr(selected_table, selected_column)
                if selected_column.type == 'int':
                    search_request = str(request.args.get('s', '', type=int)).replace('\'', '')
                else:
                    search_request = str(request.args.get('s', '')).replace('\'', '')
                print('-----------SELECTED COLUMN-------------')
                print(selected_column)
                print('-----------SELECTED COLUMN-------------')
            else:
                search_request = ''
            print('-----------SELECTED TABLE-------------')
            print(selected_table)
            print('-----------SELECTED TABLE-------------')
            for field in selected_table.__dict__:
                attr = getattr(selected_table,field)
                if isinstance(attr,metadata.BaseField) or isinstance(attr, metadata.RefField):
                    meta.append(getattr(selected_table,field))
            query = queryBuilder(selected_table,meta, selected_column, search_request).query
            print('---------QUERY----------')
            print(query)
            print('---------QUERY----------')
            cur.execute(query)
            rows = cur.fetchall()
        print('----------META------------')
        print(meta)
        print('----------META------------')
        return render_template("index.html",
            tables = tables,
            rows = rows,
            selected_table = selected_table,
            selected_column = selected_column,
            search_request = search_request,
            meta = meta)
    finally:
        con.close()

