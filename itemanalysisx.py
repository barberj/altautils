# itemanalysisx.py
"""
tokenizer for the item analysis file
"""

import os
import ply.lex as lex

# list of tokens
tokens = (
    'ITEM',
    'WORD',
    'NUMBER',
    'FLOAT',
    'LPAREN',
    'RPAREN',
    'newline',
)

# regular expression rules for simple tokens
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_ITEM = 'item\d+'
t_WORD = '[A-Za-z]+'

def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

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
