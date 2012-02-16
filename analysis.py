from __future__ import division
# analysis.py
"""
Functions to make Item analysis spreadsheet & summary document(s)
"""
import logging as log
log.root.level = log.DEBUG

from xlwt import Workbook, XFStyle, Borders, Pattern, Font
from tempfile import TemporaryFile

try:
    import erp.model as m
    import erp.model.testing as tst
except ImportError:
    import portal.model as m
    import portal.model.testing as tst

rc_type = tst.TestType.get(6)


fnt = Font()
fnt.name = 'Arial'
fnt.bold = True

style_bold = XFStyle()
style_bold.font = fnt

border_bottom = Borders()
border_bottom.bottom =  Borders.THIN

style_bold_border_bottom = XFStyle()
style_bold_border_bottom.font = fnt
style_bold_border_bottom.borders = border_bottom

border_right = Borders()
border_right.right =  Borders.THIN

style_bold_border_right = XFStyle()
style_bold_border_right.font = fnt
style_bold_border_right.borders = border_right

def write_test_header(sht):
    row = 2
    col = 3

    headers = ['Test Number', 'Date']
    for header in headers:
        sht.write(row, col, header, style_bold)
        col += 1

def version_items(version):
    version_items = {'items':{},'choices':{}}
    for section in version.sections:
        if section.archived:
            continue
        for sec_ver in section.versions:
            if sec_ver.archived:
                continue
            for item in sec_ver.items:
                if item.archived or not item.type.has_response:
                    continue
                for item_ver in item.versions:
                    if item_ver.archived:
                        continue
                    version_items['items'][item_ver.id] = {'answer':item_ver.answer, 'total': 0}
                    version_items['items'][item_ver.id]['choices'] = {}
                    for choice in item_ver.choices:
                        version_items['items'][item_ver.id]['choices'][choice.choice] = 0
                        version_items['choices'][choice.choice] = {'row':0}
                    #account for skipping
                    version_items['items'][item_ver.id]['choices'][u'-'] = 0
                    version_items['choices']['-'] = {'row':0}

    return version_items

def version_responses(ct):
    has_answer = False
    version_responses = {}
    for section in ct.sections:
        for item in section.items:
            if item.item.type.has_response:
                if item.response:
                    has_answer = True
                version_responses.setdefault(item.tst_test_item_version_id,{'response':item.response if item.response else '-'})

    if not has_answer:
        return

    return version_responses

def analyze(workbook_name='analysis.xls', binary=False, include_distratcr=True):

    _book = Workbook()
    test_count = 0
    version_count = 0
    ct_count = 0

    tboc_row = 0
    tboc = _book.add_sheet('TBOC')

    # Table of Contents
    tboc.write(tboc_row, 0,'Sheet Name', style_bold)
    tboc.write(tboc_row, 1, 'Test Name', style_bold)
    tboc.write(tboc_row, 2, 'Status', style_bold)
    tboc.write(tboc_row, 3, 'Item Count', style_bold)
    tboc.write(tboc_row, 4, 'Evaluation Count', style_bold)

    for test in rc_type.tests:
        # excel position ref
        col = 0
        row = 0

        t_ct_count = 0
        t_item_count = 0

        tboc_row += 1
        tboc.write(tboc_row, 0, test.id)
        tboc.write(tboc_row, 1, test.description)

        if test.archived or not test.versions or not [ct for v in test.versions for ct in v.candidate_tests]:
            # ignore archived tests or
            # tests with out any versions
            # or versions without candidate tests
            tboc.write(tboc_row, 2, 'Not Included')
            continue

        # start our sheet
        sheet = _book.add_sheet(str(test.id))
        sheet.write(row,col, test.description, style_bold)

        row = 1
        for version in test.versions:
            vcol = 1
            col = vcol
            if version.archived or not version.candidate_tests:
                # ignore archived
                continue

            row += 1

            # write out the version description
            sheet.write(row,0, version.description if version.description else 'Version ID %s' %  version.id, style_bold)

            # write out the item ids
            row += 1
            sheet.write(row,0, 'Test Number', style_bold)
            sheet.write(row,1, 'Date', style_bold)
            col += 1
            tiv = version_items(version)
            for item_id in tiv['items']:
                sheet.write(row,col, item_id, style_bold)
                tiv['items'][item_id]['column']=col
                col += 1

            # write out the key
            row += 1
            sheet.write(row,0, 'Key', style_bold)
            sheet.write(row,1, '-', style_bold)
            for item_id in tiv['items']:
                try:
                    sheet.write(row, tiv['items'][item_id]['column'], tiv['items'][item_id]['answer'], style_bold)
                except:
                    print tiv['items'][item_id]
                    raise

            # write out test data
            row += 1
            version_count += 1
            for candidate_test in version.candidate_tests:
                ctr = version_responses(candidate_test)
                if candidate_test.candidate_profile.account.id == 352 or not ctr:
                    # ignore alta stuff or tests with no answers
                    continue
                sheet.write(row, 0, candidate_test.number)
                sheet.write(row, 1, candidate_test.local_date.strftime('%m/%d/%Y'))
                for item_id in ctr:
                    try:
                        sheet.write(row, tiv['items'][item_id]['column'], ctr[item_id]['response'] if not binary else 1 if tiv['items'][item_id]['answer'].lower() == ctr[item_id]['response'].lower() else 0)
                        tiv['items'][item_id]['total'] += 1
                        tiv['items'][item_id]['choices'][ctr[item_id]['response']] += 1
                    except:
                        pass
                        #log.warning('Issue with Item Version ID %s for Test %s', item_id, candidate_test.number)

                row += 1
                ct_count +=1
                t_ct_count +=1

            # write out the response per item data
            row += 1
            for item_id in tiv['items']:
                sheet.write(row, tiv['items'][item_id]['column'], item_id, style_bold_border_bottom)
                t_item_count += 1

            # write out responses avail
            row += 1
            for choice in sorted(tiv['choices']):
                sheet.write(row, 1, choice, style_bold_border_right)
                tiv['choices'][choice]['row']=row
                row += 1
            for item_id in tiv['items']:
                try:
                    for choice in tiv['items'][item_id]['choices']:
                        if choice == tiv['items'][item_id]['answer']:
                            sheet.write(tiv['choices'][choice]['row'],tiv['items'][item_id]['column'],tiv['items'][item_id]['choices'][choice],style_bold)
                        else:
                            sheet.write(tiv['choices'][choice]['row'],tiv['items'][item_id]['column'],tiv['items'][item_id]['choices'][choice])
                except:
                    pass
                    #log.warning('Unable to print %s %s %s %s', test.description, test.id, item_id, tiv['items'][item_id])

            # now write out responses avail %
            row += 1
            for item_id in tiv['items']:
                sheet.write(row, tiv['items'][item_id]['column'], item_id, style_bold_border_bottom)
            row += 1
            for choice in sorted(tiv['choices']):
                sheet.write(row, 1, choice, style_bold_border_right)
                tiv['choices'][choice]['row']=row
                row += 1
            for item_id in tiv['items']:
                try:
                    for choice in tiv['items'][item_id]['choices']:
                        percent = '%0.2f %%' %  (tiv['items'][item_id]['choices'][choice] * 100/tiv['items'][item_id]['total'])
                        if choice == tiv['items'][item_id]['answer']:
                            sheet.write(tiv['choices'][choice]['row'],tiv['items'][item_id]['column'],percent,style_bold)
                        else:
                            sheet.write(tiv['choices'][choice]['row'],tiv['items'][item_id]['column'],percent)
                except:
                    pass
                    #log.warning('Unable to print %s %s %s %s', test.description, test.id, item_id, tiv['items'][item_id])

        tboc.write(tboc_row, 3, t_item_count)
        tboc.write(tboc_row, 4, t_ct_count)
        test_count += 1
    _book.save(workbook_name)
    log.debug('Analyzed %s tests containing %s versions %s candidate tests', test_count, version_count, ct_count)
