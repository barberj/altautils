# itemanalysisx.py
"""
tokenizer for the item analysis file
http://www.dabeaz.com/ply/ply.html
"""

import logging as log
log.root.level = log.DEBUG

import os
import ply.lex as lex
import ply.yacc as yacc

try:
    import erp.model.testing as tst
except ImportError:
    import portal.model.testing as tst

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
    _minscore= 'Min\s=\s+' + float_re
    t_MAXSCORE = 'Max\s=\s+' + float_re
    t_MEANSCORE = 'Mean\s=\s+' + float_re
    t_MEDIANSCORE = 'Median\s=\s+' + float_re
    t_DEVIATION = 'Standard\sDeviation\s=\s+' + float_re
    t_CRONBACH = 'Cronbach\'s\sAlpha\s+' + float_re + '\s+\(' +\
                      float_re + ',\s+' + float_re + '\)\s+' + float_re
    t_ITEM = item_header + '(' + ratio + '){4}' + '(\n' + choice +\
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

    @lex.TOKEN(_minscore)
    def t_MINSCORE(self,t):
        t.value = t.value.split('=')[1].strip()
        return t

    def t_TEST(self,t):
        r'\d+V\d+'
        test = tst.Test.get(t.value.split('V')[0])
        t.value = test.description
        self.test_name = test.description
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

    def get_tokens(self):
        """
        """
        self.tokens = []
        while True:
            tok = self.lexer.token()
            if not tok: break
            self.tokens.append(tok)
            self.token_types.add(tok.type)

            # if token is an item block
            # lets break apart the item block
            if tok.type == 'ITEM':
                self.extract_item_token_data(tok.value)

        # update our state
        self.__TOKENIZED__ = True

    def build_report(self):
        """
        """

        if not self.__TOKENIZED__:
            log.info('There are no tokens for building the report')
            return
