class RefField:
    def __init__(self, colName, referenceTable, referenceCol):
        self.colName = colName
        self.referenceTable = referenceTable
        self.referenceCol = referenceCol

class BaseField:
    def __init__(self, colName, viewedName):
        self.colName = colName
        self.viewedName = viewedName

class AUDIENCES:
    tableName = 'AUDIENCES'
    id = BaseField('id','ИД')
    name = BaseField('name', 'Аудитория')

class GROUPS:
    tableName = 'GROUPS'
    id = BaseField('id','ИД')
    name = BaseField('name', 'Группа')

class LESSONS:
    tableName = 'LESSONS'
    id = BaseField('id','ИД')
    name = BaseField('name', 'Пара')
    order_number = BaseField('order_number', 'Номер')

class LESSON_TYPES:
    tableName = 'LESSON_TYPES'
    id = BaseField('id','ИД')
    name = BaseField('name', 'Тип')

class SUBJECTS:
    tableName = 'SUBJECTS'
    id = BaseField('id','ИД')
    name = BaseField('name','Предмет')

class SUBJECT_GROUP:
    tableName = 'SUBJECT_GROUP'
    subject_id = RefField('subject_id', SUBJECTS, SUBJECTS.name)
    group_id = RefField('group_id', GROUPS, GROUPS.name)

class TEACHERS:
    tableName = 'TEACHERS'
    id = BaseField('id','ИД')
    name = BaseField('name','Преподаватель')

class WEEKDAYS:
    tableName = 'WEEKDAYS'
    id = BaseField('id','ИД')
    name = BaseField('name', 'День недели')
    order_number = BaseField('order_number', 'Номер')

#ref = S_Reference(WEEKDAYS, "id")
class SUBJECT_TEACHER():
    tableName = 'SUBJECT_TEACHER'
    subject_id = RefField('subject_id', SUBJECTS, SUBJECTS.name)
    teacher_id = RefField('teacher_id', TEACHERS, TEACHERS.name)

class SCHED_ITEMS:
    tableName = 'SCHED_ITEMS'
    id = BaseField('id','ИД')
    lesson_id = RefField('lesson_id', LESSONS, LESSONS.name)
    subject_id = RefField('subject_id', SUBJECTS, SUBJECTS.name)
    audience_id = RefField('audience_id', AUDIENCES, AUDIENCES.name)
    group_id = RefField('group_id', GROUPS, GROUPS.name)
    teacher_id = RefField('teacher_id', TEACHERS, TEACHERS.name)
    type_id = RefField('type_id', LESSON_TYPES, LESSON_TYPES.name)
    weekday_id = RefField('weekday_id', WEEKDAYS, WEEKDAYS.name)