# itemanalysisx.py
"""
tokenizer for the item analysis file
"""

import os
import ply.lex as lex
import ply.yacc as yacc

# list of tokens
tokens = (
    'ITEM',
)

# regular expression atoms
item_header = r'item\d+\s+Item'
choice = '(\s+[a-zA-Z]\(-*(1|0)\.0\))'
ratio = r'\s+(-*\d+.\d+|NaN)'

# build the full regex
item_block = item_header + '(' + ratio + '){4}' + '(\n' + choice + '(' + ratio + '){4})+'

@lex.TOKEN(item_block)
def t_ITEM(t):
    print t.value
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Error handling rule
def t_error(t):
    t.lexer.skip(1)

#Global variables
lexer = lex.lex()
tokens = []

def input_file(file_path):
    """
    """
    global lexer
    # verify file exists
    if not os.path.exists(file_path):
        raise Exception("File with path '%s' does not exist" % file_path)

    # read in the file
    data = None
    with open(file_path, 'r') as f:
        data = f.read()

    # run data through lexer
    lexer.input(data)
    return True

def get_tokens():
    """
    """
    global tokens
    while True:
        tok = lexer.token()
        if not tok: break
        tokens.append(tok)
    return tokens
