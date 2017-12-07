from flask import request
import metadata
from metadata import *

class Search:

    class Condition:
        def __init__(self,request,column,operator,order):
            self.request = request
            self.column = column
            self.operator = operator
            self.order = str(order)

    def __init__(self, table):
        self.conditions = []
        self.count = min(10, max(1,request.args.get('cnt', 1, type=int)))
        for i in range(self.count):
            temp_col = request.args.get('c' + str(i), 'id')
            temp_op = request.args.get('op' + str(i), '=')
            if not (temp_col in table.__dict__ and temp_op in operators):
                self.count -= 1
                continue
            col = getattr(table, temp_col)
            req = request.args.get('s' + str(i), '', type=int if col.type == 'int' else None)
            self.conditions.append(self.Condition(req, col, temp_op, i))

    def getRequests(self):
        list = []
        for cond in self.conditions:
            list.append(cond.request)
        return list


class QueryBuilder:
    query = ''

    def __init__(self, table, meta, search, paging):
        self.createQuery(table, meta)
        self.joinTable(table, meta)
        self.addSearchRequest(table, search)
        self.addSort(table, meta)
        self.addPage(paging, search.getRequests())

    def createQuery(self, table, meta):
        self.query = 'select %s from ' + table.tableName
        self.countQuery = 'select count(*) from ' + table.tableName
        return self.query

    def joinTable(self, table, meta):
        colsToSelect = []
        for field in meta:
            if isinstance(field, metadata.RefField):
                temp = (
                    ' left join ' + field.referenceTable.tableName + ' on '  +
                    table.tableName + '.' + field.colName +  ' = ' +
                    field.referenceTable.tableName + '.' + field.referenceTable.id.colName + '\n')
                self.query += temp
                self.countQuery += temp
                colsToSelect.append(field.referenceTable.tableName + '.' + field.referenceCol.colName)
            else:
                colsToSelect.append(table.tableName + '.' + field.colName)
        self.query = self.query % ','.join(colsToSelect)
        return self.query

    def addSearchRequest(self, table, search):
        request = []
        for cond in search.conditions:
            if cond.request != '':
                request.append('%s.%s %s ?')
                if isinstance(cond.column, metadata.RefField):
                    request[-1] = request[-1] % (cond.column.referenceTable.tableName,
                                                 cond.column.referenceCol.colName, cond.operator)
                if isinstance(cond.column, metadata.BaseField):
                    request[-1] = request[-1] % (table.tableName, cond.column.colName, cond.operator)
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

    def addPage(self, paging, params):
        paging.nextInit(self.countQuery, params)
        self.query += ' offset %d rows fetch next %d rows only'
        self.query = self.query % (paging.OnPage*paging.page, paging.OnPage)
        return self.query