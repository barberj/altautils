# itemanalysisx.py
"""
tokenizer for the item analysis file
http://www.dabeaz.com/ply/ply.html
"""

import logging as log
log.root.level = log.DEBUG

import os
from datetime import datetime
from itertools import count
import ply.lex as lex
from xlwt import Workbook, XFStyle, Borders, Pattern, Font

try:
    import erp.model.testing as tst
except ImportError:
    import portal.model.testing as tst

class CounterWrapper(object):
    def __init__(self, wrapped_class, *args, **kwargs):
        self.wrapped_class = wrapped_class(*args, **kwargs)

    def __getattr__(self, attr):
        orig_attr = self.wrapped_class.__getattribute__(attr)
        return orig_attr

    @property
    def current(self):
        import re
        next_val = int(re.search('\d+',repr(self.wrapped_class)).group())
        return next_val - 1

    def __repr__(self):
        return str(self.current)

class itemAnalysisLexer(object):
    # state variables
    __BUILT__ = False
    __TOKENIZED__ = False

    # list of tokens
    tokens = (
        'ITEM',
        'TEST',
        'ITEMCOUNT',
        'EXAMINEECOUNT',
        'MINSCORE',
        'MAXSCORE',
        'MEANSCORE',
        'MEDIANSCORE',
        'DEVIATION',
        'CRONBACH'
    )

    # regular expression atoms
    float_re = r'(-{0,1}\d+(.\d+){0,1})' # could be an int as well since i have the decimal in parens and allow for 0 count
    item_header = r'item\d+\s+Item'
    choice = '(\s+[a-zA-Z]\(-*(1|0)\.0\))'
    ratio = r'\s+(' + float_re + '|NaN)'

    # build the full regexes
    t_ITEMCOUNT = 'Number\sof\sItems\s=\s+\d+'
    t_EXAMINEECOUNT = 'Number\sof\sExaminees\s=\s+\d+'
    t_MINSCORE= 'Min\s=\s+' + float_re
    t_MAXSCORE = 'Max\s=\s+' + float_re
    t_MEANSCORE = 'Mean\s=\s+' + float_re
    t_MEDIANSCORE = 'Median\s=\s+' + float_re
    t_DEVIATION = 'Standard\sDeviation\s=\s+' + float_re
    t_CRONBACH = 'Cronbach\'s\sAlpha\s+' + float_re + '\s+\(' +\
                      float_re + ',\s+' + float_re + '\)\s+' + float_re
    _item = item_header + '(' + ratio + '){4}' + '(\n' + choice +\
                      '(' + ratio + '){4})+'

    # globals for the report
    test_name = ''
    item_level_stats = {}

    # lets keep track of what token
    # types we have seen
    token_types = set()

    def __init__(self,file_path=None):
        if file_path:
            self.input_file(file_path)

    def t_TEST(self,t):
        r'\d+V\d+'
        test = tst.Test.get(t.value.split('V')[0])
        t.value = test.description
        self.test_name = test.description
        return t

    @lex.TOKEN(_item)
    def t_ITEM(self,t):
        t.value = self.extract_item_token_data(t.value)
        return t

    def t_newline(self,t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Error handling rule
    def t_error(self,t):
        t.lexer.skip(1)

    def input_file(self,file_path):
        """
        Build lexer and run file through
        """
        # only build lexer once
        if self.__BUILT__:
            return

        if not file_path:
            raise Exception('File path must be provided to run throught the lexer')
        if not isinstance(file_path, str):
            raise Exception('File path must be a string')
        log.debug('Building lexer')

        # verify file exists
        if not os.path.exists(file_path):
            raise Exception("File with path '%s' does not exist" % file_path)

        # read in the file
        data = None
        with open(file_path, 'r') as f:
            data = f.read()

        # run data through lexer
        self.lexer = lex.lex(module=self)
        self.lexer.input(data)
        self.__BUILT__ = True

    def extract_item_token_data(self, token):
        """
        Get all the analysis data from the item token

        Sample token:
        item84212             Item      0.5000      0.5477      0.9258      1.1603
                             a(0.0)      0.3333      0.5164     -0.6478     -0.8399
                             b(1.0)      0.5000      0.5477      0.9258      1.1603
                             c(0.0)      0.0000      0.0000         NaN         NaN
                             d(0.0)      0.1667      0.4082     -0.6758     -1.0081

        First line of token will have the item defaults.
        Column 0 has the item number prefixed with the word item.
        Column 2 has the Difficulty.
        Column 4 has the Item-Total Pearson.

        Subsequent rows have the item choice details.
        Column 0 has the choice
        Column 1 has the Difficulty (also known as p-value).
        Column 3 has the Item-Total Pearson.
        """

        # break on new lines...
        item_parts = token.split('\n')

        # first line has the item stats
        header = item_parts[0].split()
        item = header[0][4:]
        difficulty = header[2]
        pearson = header[4]
        choices = {}

        self.item_level_stats[item] = {'difficulty':difficulty,
                                        'pearson':pearson, 'choices':choices}

        # remaining lines have the choice stats
        for choice_line in item_parts[1:]:
            choice_parts = choice_line.split()

            # first character of the first part ... choice_parts[0][0]
            # is going to be the choice ... ie (a)
            # third character of the first part ... choice_parts[0][2]
            # will determine if that choice is the answer. Labeled on the
            # report as score for some reason
            choices[choice_parts[0][0]] = {'difficulty':choice_parts[1],
                            'pearson':choice_parts[3],
                            'answer':choice_parts[0][2]}

        return self.item_level_stats[item]

    def get_tokens(self):
        """
        """
        self.tokens = []
        while True:
            tok = self.lexer.token()
            if not tok: break

            # score and counts we only care about the number
            # the type infers the rest
            if 'SCORE' in tok.type or 'COUNT' in tok.type or \
                'DEVIATION' in tok.type:
                tok.value = tok.value.split('=')[1].strip()

            self.tokens.append(tok)
            # keeping up with types seen
            # mainly for debug
            self.token_types.add(tok.type)

        # update our state
        self.__TOKENIZED__ = True

    def build_report(self):
        """
        """

        if not self.__TOKENIZED__:
            log.info('There are no tokens for building the report')
            return

        book = Workbook()
        sheet = book.add_sheet('ItemAnalysis')
        row = CounterWrapper(count)
        sheet.write(row.next(),0,'ALTA Item Analysis Report')
        sheet.write(row.next(),0,self.test_name)
        sheet.write(row.next(),0,'Report Date %s' % datetime.now().strftime('%B %d, %Y'))
        # Testing dates ...

        sheet.write(row.next(),0, 'Item Level Statistics')

        sheet.write(row.next(),0, 'Item')
        sheet.write(row.current,1, 'Difficulty')
        sheet.write(row.current,2, 'Item-Total Correlation')

        for level in sorted(self.item_level_stats.keys()):
            sheet.write(row.next(),0, level)
            sheet.write(row.current,1, self.item_level_stats[level]['difficulty'])
            sheet.write(row.current,2, self.item_level_stats[level]['pearson'])
            self.item_level_stats[level]

        sheet.write(row.next(),0, 'Test Level  Statistics')

        sheet.write(row.next(),0, 'Number of Items')
        sheet.write(row.current,1,2)

        book.save('%s IAE.xls' % self.test_name)

    @classmethod
    def analyze(cls,file_path=None):

        if not file_path:
            raise Exception('File path must be provided to analyze with lexer')

        item_analyzer = cls(file_path)
        item_analyzer.get_tokens()
        item_analyzer.build_report()

        return item_analyzer
