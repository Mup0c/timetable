import fdb
from flask import Flask
from flask import request
from flask import render_template
app = Flask(__name__)
DB_PATH = 'localhost:C:/Users/mir-o/cloud/db/TIMETABLE.FDB'

class Room:
    table = 'AUDIENCES'
    id = ['Int','ИД']
    name = ['String', 'Аудитория']

class Group:
    table = 'GROUPS'
    id = ['Int','ИД']
    name = ['String', 'Группа']

class Lesson:
    table = 'LESSONS'
    id = ['Int','ИД']
    name = ['String', 'Пара']
    order_number = ['Int', 'Номер']

class Lesson_type:
    table = 'LESSON_TYPES'
    id = ['Int','ИД']
    name = ['String', 'Тип']

class Subject:
    table = 'SUBJECTS'
    id = ['Int','ИД']
    name = ['String', 'Предмет']

class Subject_group:
    table = 'SUBJECT_GROUP'
    subject_id = ['Ref', Subject]
    group_id = ['Ref', Group]

class Teacher:
    table = 'TEACHERS'
    id = ['Int','ИД']
    name = ['String', 'Преподаватель']

class Weekday:
    table = 'WEEKDAYS'
    id = ['Int','ИД']
    name = ['String', 'День недели']
    order_number = ['Int', 'Номер']

class Subject_teacher:
    table = 'SUBJECT_TEACHER'
    subject_id = ['Ref', Subject]
    teacher_id = ['Ref', Teacher]

class Sched_Item:
    table = 'SCHED_ITEMS'
    id = ['Int','ИД']
    lesson_id = ['Ref',Lesson]
    subject_id = ['Ref', Subject]
    audience_id = ['Ref', Room]
    group_id = ['Ref', Group]
    teacher_id = ['Ref', Teacher]
    type_id = ['Ref', Lesson_type]
    weekday_id = ['Ref', Weekday]

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

        cur.execute('''select RDB$RELATION_NAME from RDB$RELATIONS
                        where (RDB$SYSTEM_FLAG = 0) AND (RDB$RELATION_TYPE = 0)
                        order by RDB$RELATION_NAME''')
        tables = []
        for row in cur.fetchall():
            str_name = str(row[0]).strip()
            tables.append(str_name)

        selected_table = request.args.get('t', '')
        if selected_table in tables:
            table_fields = []
            cur.execute('''select RDB$FIELD_NAME
                    from RDB$RELATION_FIELDS
                    where RDB$SYSTEM_FLAG = 0 and RDB$RELATION_NAME ='%s'
                    order by RDB$FIELD_POSITION'''%selected_table)
            for row in cur.fetchall():
                str_name = str(row[0]).strip()
                table_fields.append(str_name)
            print(table_fields)
            cur.execute('select * from ' + selected_table)
        return render_template("index.html",
            tables = tables,
            result = cur.fetchall(),
            selected_table = selected_table,
            table_fields = table_fields)
    finally:
        con.close()


