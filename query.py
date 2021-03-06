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
        return [cond.request for cond in self.conditions]


class QueryBuilder:
    countQuery = 'select count(*) from '

    def getTableRows(self, table):
        return 'select * from ' + table.tableName

    def getAnalyticsView(self, table, meta, search):
        query = self.createQuery(table, meta)
        query = query % self.addColsToSelect_analytics(table, meta)
        query += self.joinTable(table, meta)
        query += self.addSearchRequest(table, search)
        return query

    def getTableView(self, table, meta, search, paging, sortCol):
        query = self.createQuery(table, meta)
        query = query % self.addColsToSelect(table, meta)
        query += self.joinTable(table, meta)
        query += self.addSearchRequest(table, search)
        query += self.addSort(table, meta, sortCol)
        query += self.addPage(paging, search.getRequests())
        return query

    def createQuery(self, table, meta):
        query = 'select %s from ' + table.tableName
        self.countQuery += table.tableName
        return query

    def addColsToSelect_analytics(self, table, meta):
        return ','.join((field.referenceTable.tableName + '.' + field.referenceCol.colName + ',' + table.tableName + '.' + field.colName)
                        if isinstance(field, metadata.RefField) else
                        (table.tableName + '.' + field.colName)
                        for field in meta)

    def addColsToSelect(self, table, meta):
        return ','.join(
            field.referenceTable.tableName + '.' + field.referenceCol.colName
            if isinstance(field, metadata.RefField)
            else table.tableName + '.' + field.colName
                for field in meta)

    def addColsToSelectNoFK(self, table, meta):
        return ','.join(table.tableName + '.' + field.colName for field in meta)

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


    def addSort(self, table, meta, sortCol):
        query = ''
        col = sortCol
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
            if ctype == "ref_ord":
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
        query = self.createQuery(table, meta)
        query = query % self.addColsToSelectNoFK(table, meta)
        query += (' where %s.id = ' + str(id)) % table.tableName
        return query

    def getUpdate(self, table, id, meta):
        query = 'update %s set\n' % table.tableName
        exps = ['%s = ?' % field.colName for field in meta]
        query +=  ','.join(exps)
        query += '\nwhere ID = ' + str(id)
        return query

    def getInsert(self, table, meta, conflict = False):
        query = 'insert into %s ' % table if conflict else table.tableName
        query += '(%s) ' % ','.join(field if conflict else field.colName for field in meta)
        query += 'values (?%s)' % (',?'*(len(meta)-1))
        return query

    def getConflict(self, table, meta, type_id):
        query = 'select c.CONFLICT_GROUP_ID,%s from CONFLICTS c ' % self.addColsToSelect(table,meta)
        query += 'inner join SCHED_ITEMS on c.SCHED_ITEM_ID = SCHED_ITEMS.ID '
        query += self.joinTable(table, meta)
        query += ' where c.CONFLICT_TYPE_ID = %d' % type_id
        return query

    def getConflictingIDs(self):
        query = 'SELECT c.SCHED_ITEM_ID FROM CONFLICTS c'
        return query

    def createConflict(self, fields):
        query = 'select ID,'
        query += ','.join('t1.' + field for field in fields)
        query += ' from SCHED_ITEMS t1 where exists (select * from SCHED_ITEMS t2 where '
        query += ' AND '.join('t1.%s = t2.%s' % (field, field) for field in fields)
        query += ' AND t1.ID <> t2.ID)'
        query += ' GROUP BY %s,ID' % ','.join(fields)
        return query
