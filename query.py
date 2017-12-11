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

    def getTableView(self, table, meta, search, paging):
        query = self.createQuery(table, meta)
        query = query % self.addColsToSelect(table, meta)
        query += self.joinTable(table, meta)
        query += self.addSearchRequest(table, search)
        query += self.addSort(table, meta)
        query += self.addPage(paging, search.getRequests())
        return query

    def createQuery(self, table, meta):
        query = 'select %s from ' + table.tableName
        self.countQuery = 'select count(*) from ' + table.tableName
        return query

    def addColsToSelect(self, table, meta):
        colsToSelect = []
        for field in meta:
            if isinstance(field, metadata.RefField):
                colsToSelect.append(field.referenceTable.tableName + '.' + field.referenceCol.colName)
            else:
                colsToSelect.append(table.tableName + '.' + field.colName)
        return ','.join(colsToSelect)

    def joinTable(self, table, meta):
        query = ''
        for field in meta:
            if isinstance(field, metadata.RefField):
                temp = (
                    ' left join ' + field.referenceTable.tableName + ' on '  +
                    table.tableName + '.' + field.colName +  ' = ' +
                    field.referenceTable.tableName + '.' + field.referenceTable.id.colName + '\n')
                query += temp
                self.countQuery += temp
        return query

    def addSearchRequest(self, table, search):
        request = []
        query = ''
        haveConditions = False
        for cond in search.conditions:
            if cond.request != '':
                request.append('%s.%s %s ?')
                if isinstance(cond.column, metadata.RefField):
                    request[-1] = request[-1] % (cond.column.referenceTable.tableName,
                                                 cond.column.referenceCol.colName, cond.operator)
                elif isinstance(cond.column, metadata.BaseField):
                    request[-1] = request[-1] % (table.tableName, cond.column.colName, cond.operator)
                haveConditions = True
        if haveConditions:
            temp = ' where ' + ' and '.join(request)
            query += temp
            self.countQuery += temp
        return query


    def addSort(self, table, meta):
        query = ''
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
            query = ' order by %s.%s'
            if ctype == "reford":
                query += ', %s.%s'
                query = query % (tname, "order_number", tname, cname)
            else:
                query = query % (tname, cname)
        return query

    def addPage(self, paging, params):
        query = ''
        paging.nextInit(self.countQuery, params)
        query += ' offset %d rows fetch next %d rows only'
        query = query % (paging.onPage*paging.page, paging.onPage)
        return query

    def getRowToModify(self, table, id, meta):
        pass