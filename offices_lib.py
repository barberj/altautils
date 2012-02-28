#offices_lib.py

import logging as log
log.root.level = log.DEBUG

from xlrd import open_workbook

import erp.model as m
import erp.model.testing as tst

def getTMZ(time_zone):
    """
    Get the corresponding time zone
    for the given abbreviation

    EST == American/New York
    """

    if time_zone == 'Puerto Rico (AST)':
        return m.misc.TimeZone.get(22)

    if time_zone == 'EST':
        return m.misc.TimeZone.get(23)

    if time_zone == 'CST':
        return m.misc.TimeZone.get(24)

    if time_zone == 'MST':
        return m.misc.TimeZone.get(25)

    if time_zone == 'PST':
        return m.misc.TimeZone.get(26)

    if time_zone == 'Arizona':
        return m.misc.TimeZone.get(26)

def fog1007():

    offices_added = 0

    # parent accounts to add offices to
    acquisition = m.Account.get(24346).testing_account
    collections = m.Account.get(23125).testing_account
    
    # data set with offices to add
    sheet = open_workbook('redcross.xls').sheet_by_index(0)

    # lets add the offices
    for row in range(1,sheet.nrows):
        collections_office =  sheet.cell(row,1).value.strip()
        collections_office_tmz =  sheet.cell(row,2).value
        acquistions_office  = sheet.cell(row,3).value.strip()

        if collections_office:
            offices_added += 1
            tst.Office(name=collections_office, time_zone=getTMZ(collections_office_tmz), account=collections)

        if acquistions_office:
            offices_added += 1
            tst.Office(name=acquistions_office, account=acquisition)
    
    log.info('Added %s new offices', offices_added)
