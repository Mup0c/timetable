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

class BaseField:
    def __init__(self, colName, viewedName, type):
        self.type = type
        self.colName = colName
        self.viewedName = viewedName

class RefField(BaseField):
    def __init__(self, colName, referenceTable, referenceCol):
        super().__init__(colName, viewedName = referenceCol.viewedName, type = None)
        self.referenceTable = referenceTable
        self.referenceCol = referenceCol

class AUDIENCES:
    tableName = 'AUDIENCES'
    id = BaseField('id','ИД', 'int')
    name = BaseField('name', 'Аудитория', 'str')

class GROUPS:
    tableName = 'GROUPS'
    id = BaseField('id','ИД', 'int')
    name = BaseField('name', 'Группа', 'str')

class LESSONS:
    tableName = 'LESSONS'
    id = BaseField('id','ИД', 'int')
    name = BaseField('name', 'Пара', 'reford')
    order_number = BaseField('order_number', 'Номер', 'str')

class LESSON_TYPES:
    tableName = 'LESSON_TYPES'
    id = BaseField('id','ИД', 'int')
    name = BaseField('name', 'Тип', 'str')

class SUBJECTS:
    tableName = 'SUBJECTS'
    id = BaseField('id','ИД', 'int')
    name = BaseField('name','Предмет', 'str')

class SUBJECT_GROUP:
    tableName = 'SUBJECT_GROUP'
    subject_id = RefField('subject_id', SUBJECTS, SUBJECTS.name)
    group_id = RefField('group_id', GROUPS, GROUPS.name)

class TEACHERS:
    tableName = 'TEACHERS'
    id = BaseField('id','ИД', 'int')
    name = BaseField('name','Преподаватель', 'str')

class WEEKDAYS:
    tableName = 'WEEKDAYS'
    id = BaseField('id','ИД', 'int')
    name = BaseField('name', 'День недели', 'reford')
    order_number = BaseField('order_number', 'Номер', 'int')

class SUBJECT_TEACHER:
    tableName = 'SUBJECT_TEACHER'
    subject_id = RefField('subject_id', SUBJECTS, SUBJECTS.name)
    teacher_id = RefField('teacher_id', TEACHERS, TEACHERS.name)

class SCHED_ITEMS:
    tableName = 'SCHED_ITEMS'
    id = BaseField('id','ИД', 'int')
    lesson_id = RefField('lesson_id', LESSONS, LESSONS.name)
    subject_id = RefField('subject_id', SUBJECTS, SUBJECTS.name)
    audience_id = RefField('audience_id', AUDIENCES, AUDIENCES.name)
    group_id = RefField('group_id', GROUPS, GROUPS.name)
    teacher_id = RefField('teacher_id', TEACHERS, TEACHERS.name)
    type_id = RefField('type_id', LESSON_TYPES, LESSON_TYPES.name)
    weekday_id = RefField('weekday_id', WEEKDAYS, WEEKDAYS.name)