#decorator
class AUDIENCES:
    table = 'AUDIENCES'
    id = ['Int','ИД']
    name = ['String', 'Аудитория']

class GROUPS:
    table = 'GROUPS'
    id = ['Int','ИД']
    name = ['String', 'Группа']

class LESSONS:
    table = 'LESSONS'
    id = ['Int','ИД']
    name = ['String', 'Пара']
    order_number = ['Int', 'Номер']

class LESSON_TYPES:
    table = 'LESSON_TYPES'
    id = ['Int','ИД']
    name = ['String', 'Тип']

class SUBJECTS:
    table = 'SUBJECTS'
    id = ['Int','ИД']
    name = ['String', 'Предмет']

class SUBJECT_GROUP:
    table = 'SUBJECT_GROUP'
    subject_id = ['Ref', SUBJECTS]
    group_id = ['Ref', GROUPS]

class TEACHERS:
    table = 'TEACHERS'
    id = ['Int','ИД']
    name = ['String', 'Преподаватель']

class WEEKDAYS:
    table = 'WEEKDAYS'
    columns = {}
    columns["id"] = 'ИД'
    columns["String"] = 'День недели'
    columns["order_number"] = 'Номер'
    id = ['Int']
    name = ['String']
    order_number = ['Int', 'Номер']

#ref = S_Reference(WEEKDAYS, "id")
class SUBJECT_TEACHER:
    table = 'SUBJECT_TEACHER'
    subject_id = ['Ref', SUBJECTS]
    teacher_id = ['Ref', TEACHERS]

class SCHED_ITEMS:
    table = 'SCHED_ITEMS'
    id = ['Int','ИД']
    lesson_id = ['Ref',LESSONS]
    subject_id = ['Ref', SUBJECTS]
    audience_id = ['Ref', AUDIENCES]
    group_id = ['Ref', GROUPS]
    teacher_id = ['Ref', TEACHERS]
    type_id = ['Ref', LESSON_TYPES]
    weekday_id = ['Ref', WEEKDAYS]