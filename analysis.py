from __future__ import division
# analysis.py
"""
Functions to make Item analysis spreadsheet & summary document(s)
"""
import logging as log
log.root.level = log.DEBUG

from xlwt import Workbook, XFStyle, Borders, Pattern, Font
from tempfile import TemporaryFile

from sqlalchemy import and_, or_, distinct, asc
from sqlalchemy.orm import eagerload, eagerload_all

try:
    import erp.model as m
    import erp.model.testing as tst
except ImportError:
    import portal.model as m
    import portal.model.testing as tst

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

def version_items(version):
    """
    Return dictionary with item answer,
    all the choices the version has available, and
    corresponding counts
    """
    version_items = {'choices':{}}
    for section in version.sections:
        if section.archived:
            continue
        for sec_ver in section.versions:
            if sec_ver.archived:
                continue
            for item in sec_ver.items:
                if item.archived or not item.type.has_response or not item.type.has_choices:
                    continue
                for item_ver in item.versions:
                    if item_ver.archived:
                        continue
                    version_items[item_ver.id] = {'answer':item_ver.answer, 'total': 0}
                    version_items[item_ver.id]['choices'] = {}
                    for choice in item_ver.choices:
                        version_items[item_ver.id]['choices'][choice.choice] = 0
                        version_items['choices'][choice.choice] = {'row':0}
                    #account for skipping
                    version_items[item_ver.id]['choices'][u'-'] = 0
                    version_items['choices']['-'] = {'row':0}

    return version_items

def candidate_responses(candidate_test):
    """
    Dictionary of responses for the candidate test.
    Key is the item id, value is the response
    """
    responses = {}
    for section in candidate_test.sections:
        if section.version and section.version.archived:
            # archived items won't be tested on any longer
            # no point in including in analysis
            continue
        for item in section.items:
            if item.item.type.has_response and item.item.type.has_choices:
                responses[item.version.id] = item.response if item.response else '-'
    return responses

def get_tests_query(filter_object=None):

    # get the candidate tests to page through
    query = tst.CandidateTest.query

    # leave out alta tests
    query = query.join('candidate_profile','account')
    query = query.filter(tst.Account.id!=352)

    # leave out archived
    query = query.join('test','test','type')
    query = query.join('version')
    query = query.filter(and_(tst.AccountTest.archived==False, tst.Test.archived==False, tst.TestVersion.archived==False))

    # get only reading comprehension
    query = query.filter(tst.TestType.id==6)

    # ensure there are responses
    query = query.join('sections','items')
    query = query.filter(and_(tst.CandidateTestItem.response!=None, tst.CandidateTestItem.response!=''))

    # order by test version
    query = query.order_by(asc(tst.Test.id),asc(tst.TestVersion.id))

    # eagerload our responses
    query = query.options(eagerload_all('sections.items'), eagerload('sections.items.item.type.has_response'))

    return query.distinct()

def get_test_ids():
    # get the candidate test ids
    query = m.meta.Session.query(distinct(tst.CandidateTest.id))

    # leave out alta tests
    query = query.join('candidate_profile','account')
    query = query.filter(tst.Account.id!=352)

    # leave out archived
    query = query.join('test','test','type')
    query = query.join('version')
    query = query.filter(and_(tst.AccountTest.archived==False, tst.Test.archived==False, tst.TestVersion.archived==False))

    # get only reading comprehension
    query = query.filter(tst.TestType.id==6)

    # ensure there are responses
    query = query.join('sections','items')
    query = query.filter(and_(tst.CandidateTestItem.response!=None, tst.CandidateTestItem.response!=''))

    # order by test version
    query = query.order_by(asc(tst.TestVersion.id))

    # query gives us a list or sets
    # use list comprehension to return just a list
    result_rows = query.all()
    return [row[0] for row in result_rows]

class AnalysisDoc(object):

    test_count = 0
    version_count = 0
    ct_count = 0

    def __init__(self):
        pass

    def add_test(self):
        pass

class page(dict):

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs )
        self['row']=0
        self['col']=0

    def __getattr__(self, key):
        """
        Return the attribute value if it exists
        Else None
        """
        if key in self:
            return self[key]
        return None

    def __setattr__(self, key, value):
        """
        If the attribute exists, update
        Else create
        """
        self[key] = value

    def get(self, key):
        """
        Return the key value if it exists
        Else None
        """
        if key in self:
            return self[key]
        else:
            return None

class AnalysisWB(AnalysisDoc):

    _book = None

    name = ''

    tboc = None
    pages = {}

    def __init__(self, name='analysis.xls'):
        """
        Initialize our Analysis Document
        """

        self.name = name
        self._book = Workbook()

        # create table of contents
        self.create_table_of_contents()

    def get_page(self,name):
        """
        Returns the page object containing the
        sheet reference, last row and column position.

        If the page with provided name doesn't exist
        it creates it and returns the default values.
        """
        cur_page = self.pages.setdefault(name,page())
        if not cur_page.sheet:
            cur_page.sheet = self._book.add_sheet(name)
        return cur_page

    def create_table_of_contents(self):
        # create the sheet
        tboc = self.get_page('TBOC')

        # add the headers
        tboc.sheet.write(tboc.row, 0,'Sheet Name', style_bold)
        tboc.sheet.write(tboc.row, 1, 'Test Name', style_bold)
        tboc.sheet.write(tboc.row, 2, 'Item Count', style_bold)
        tboc.sheet.write(tboc.row, 3, 'Evaluation Count', style_bold)

        # increment to ready for entry
        tboc.row += 2

    def update_tboc(self, test_page):

        tboc = self.get_page('TBOC')
        # add the test
        tboc.sheet.write(tboc.row, 0, '%sv%s' % (test_page['test'].id, test_page['version'].id))
        tboc.sheet.write(tboc.row, 1, test_page['test'].description)
        # don't include the choices in the item count
        tboc.sheet.write(tboc.row, 2, len(test_page['items'].keys())-1)
        tboc.sheet.write(tboc.row, 3, test_page['ct_count'])

        # increment to ready for entry
        tboc.row += 1

    def add_test(self,candidate_test):
        self.ct_count += 1

        # some tests may have multiple verions
        # currently they want each verison to have its own page
        # for indiviudal analysis
        _name= '%sv%s' % (candidate_test.test.test.id, candidate_test.version.id)
        test_page = self.get_page(_name)
        if not test_page.ct_count:
            # version just added to workbook
            test_page.ct_count = 0
            test_page.test = candidate_test.test.test
            test_page.version = candidate_test.version
            test_page.items = version_items(test_page.version)

        # collate candidate test data
        ct_responses = candidate_responses(candidate_test)
        for response in ct_responses:
            test_page['items'][response]['choices'][ct_responses[response]] += 1
            test_page['items'][response]['total'] += 1
        test_page.ct_count += 1

    def close(self,):
        # save before closing
        self._book.save(self.name)

def analyze(workbook_name='analysis.xls', binary=False, include_distratcr=True):

    query = get_tests_query()

    total = query.count()
    limit = 500
    offset = 0

    alpha = AnalysisWB('alpha_analysis.xls')

    while offset < total:
        # get the tests
        tests = query.limit(limit).offset(offset).all()

        # update our offset
        offset += limit

        # do something with the tests
        for test in tests:
            alpha.add_test(test)

    # lets update the tboc
    # sort by test and then version
    for page in sorted(alpha.pages, key=lambda test_page: (alpha.pages[test_page]['test'].id,alpha.pages[test_page]['version'].id) if test_page != 'TBOC' else 0):
        if page != 'TBOC':
            alpha.update_tboc(alpha.pages[page])

    alpha.close()

    for test in []:

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
                if candidate_test.test.archived or candidate_test.candidate_profile.account.id == 352 or not ctr:
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
                test_ids.append(candidate_test.id)
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
