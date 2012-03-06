from __future__ import division
# analysis.py
"""
Functions to make Item analysis spreadsheets
"""
import logging as log
log.root.level = log.DEBUG

from xlwt import Workbook, XFStyle, Borders, Pattern, Font

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
                    version_items[item_ver.id] = {'answer':item_ver.answer, 'total': 0, 'section': sec_ver.id}
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
    #query = query.filter(tst.Account.id!=352)
    query = query.filter(tst.Account.id==957)

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
    query = query.order_by(asc(tst.Test.id),asc(tst.TestVersion.id),asc(tst.CandidateTest.local_date))

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

    def next_row(self):
        self['row'] += 1
        self['col'] = 0

class AnalysisWB(AnalysisDoc):

    _book = None

    name = ''

    tboc = None
    pages = {}

    def __init__(self, name='analysis.xls', raw=True, binary=False):
        """
        Initialize our Analysis Document
        """

        self.name = name
        self._book = Workbook()
        self.raw = raw
        self.binary = binary

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

    def add_items(self,test_page):
        """
        Add the column header
        """

        if not self.raw:
            # if doing items for details
            # we need to make space
            # for the ct number, date
            test_page.col = 2

        for item in test_page['items']:
            if item != 'choices':
                if not self.raw:
                    test_page.sheet.write(test_page.row-2, test_page.col, u'section %s' % test_page['items'][item]['section'], style_bold)
                test_page.sheet.write(test_page.row, test_page.col, u'item %s' % item, style_bold)
                # need to keep up with the items position
                # so that the correlating responses
                # will be in right column as well
                test_page['items'][item]['col'] = test_page.col
                test_page.col += 1

        # increment row, reset column
        test_page.next_row()

    def add_distractor(self, test_page, use_percentage = False):

        test_page.next_row()

        for choice in sorted(test_page['items']['choices']):
            # ignore the designation for no answer
            test_page.sheet.write(test_page.row, 1, choice, style_bold_border_right)

            # in next col print all the item ids
            # with this choice as the correct answer
            for item in test_page['items']:
                 if item != 'choices':
                    for t_choice in test_page['items'][item]['choices']:
                        if t_choice == choice:
                            test_page.sheet.write(test_page.row,
                                test_page['items'][item]['col'],
                                0 if not test_page['items'][item]['total'] or not test_page['items'][item]['choices'][choice] else
                                1 if test_page['items'][item]['choices'][choice] and not use_percentage else
                                '%0.2f %%' % (test_page['items'][item]['choices'][choice] * 100 /  test_page['items'][item]['total']))
            test_page.next_row()

    def add_description(self, test_page):
        test_page.sheet.write(test_page.row, 0, test_page['test'].description)
        test_page.next_row()

    def add_available_responses(self, test_page):

        for choice in sorted(test_page['items']['choices']):
            # ignore the designation for no answer
            if not choice == '-':
                test_page.sheet.write(test_page.row, 1, choice)

                # in next col print all the item ids
                # with this choice as the correct answer
                items = [item for item in test_page['items'] if item != 'choices' and
                            test_page['items'][item]['answer'] == choice]
                item_str = ''
                for item in items:
                    item_str += '%s,' % item
                # remove trailing comma
                item_str = item_str[:-1]
                test_page.sheet.write(test_page.row, 2, item_str)
                test_page.next_row()

    def add_test(self,candidate_test):

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

            if not self.raw:
                # add the available responses
                self.add_available_responses(test_page)

                # add the description
                self.add_description(test_page)

                # add key, name, candidate test and date info
                test_page.sheet.write(test_page.row, test_page.col, 'Key', style_bold)
                test_page.sheet.write(test_page.row, test_page.col + 1, '-', style_bold)

                # increment row, reset column
                test_page.next_row()

            # now add the items
            self.add_items(test_page)

            if not self.raw:
                # add the correct answer above the item
                for item in test_page['items']:
                    if item != 'choices':
                        test_page.sheet.write(test_page.row-2,
                            test_page['items'][item]['col'],
                            test_page['items'][item]['answer'])

                # freeze frame
                test_page.sheet.set_panes_frozen(True)
                test_page.sheet.set_horz_split_pos(test_page.row)
                test_page.sheet.set_remove_splits(True)

        if not self.raw:
            # we want details, not just raw responses
            # add candidate test and date info
            test_page.sheet.write(test_page.row, test_page.col, candidate_test.number)
            test_page.sheet.write(test_page.row, test_page.col + 1, candidate_test.local_date.strftime('%m/%d/%Y'))
            test_page.col += 2

        # collate candidate test data
        ct_items = candidate_responses(candidate_test)
        for item_number in ct_items:
            # keep response tallies so can do stats
            test_page['items'][item_number]['choices'][ct_items[item_number]] += 1
            test_page['items'][item_number]['total'] += 1
            # write the response on sheet
            try:
                test_page.sheet.write(test_page.row, test_page['items'][item_number]['col'],
                    ct_items[item_number] if not self.binary else 1
                    if test_page['items'][item_number]['answer'] == ct_items[item_number] else 0)
            except:
                print test_page['items'][item_number]['col']
                print test_page.row, test_page.col
                raise

        # increment row, reset column
        test_page.next_row()
        # add one more evaluation to the
        # version tally
        test_page.ct_count += 1
        # and total tally
        self.ct_count += 1

    def close(self,):
        # save before closing
        self._book.save(self.name)

def analyze_detail():
    # get the alpha detail with distractors
    return analyze(workbook_name='alpha_analysis.xls', raw=False)

def analyze_raw():
    # get the raw
    return analyze(workbook_name='raw_responses.xls')

def analyze(workbook_name, raw=True, binary=False):

    query = get_tests_query()

    total = query.count()
    limit = 500
    offset = 0

    wb = AnalysisWB(workbook_name,raw,binary)

    while offset < total:
        # get the tests
        tests = query.limit(limit).offset(offset).all()

        # update our offset
        offset += limit

        # do something with the tests
        for test in tests:
            wb.add_test(test)

    # lets update the tboc
    # and add distractor data if applicable
    # sort by test and then version
    for page_name in sorted(wb.pages, key=lambda test_page: (wb.pages[test_page]['test'].id,wb.pages[test_page]['version'].id) if test_page != 'TBOC' else 0):
        if page_name != 'TBOC':
            test_page = wb.pages[page_name]
            wb.update_tboc(test_page)
            if not wb.raw:
                # add the distractors
                wb.add_distractor(test_page)
                # now as percentages
                wb.add_distractor(test_page, use_percentage=True)

    wb.close()

    return wb
