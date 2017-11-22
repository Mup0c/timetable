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

    def __init__(self, table, meta):
        self.createQuery(table, meta)
        self.joinTable(table, meta)

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
        table_fields = []
        rows = []
        meta = []
        if selected_table in tables:
            selected_table = getattr(metadata,selected_table)
            print('------------------------')
            print(selected_table)
            for field in selected_table.__dict__:
                if isinstance(getattr(selected_table,field),metadata.BaseField):
                    meta.append(getattr(selected_table,field))
                    table_fields.append(getattr(selected_table,field).viewedName)
                if isinstance(getattr(selected_table,field),metadata.RefField):
                    meta.append(getattr(selected_table, field))
                    table_fields.append(getattr(selected_table,field).referenceCol.viewedName)
            #cur.execute('select * from ' + selected_table.tableName)
            query = queryBuilder(selected_table,meta).query
            print('---------QUERY\/----------')
            print(query)
            print('---------QUERY/\--------')
            cur.execute(query)
            rows = cur.fetchall()
        print('------------------------')
        print(meta)
        return render_template("index.html",
            tables = tables,
            rows = rows,
            selected_table = selected_table,
            table_fields = table_fields)
    finally:
        con.close()