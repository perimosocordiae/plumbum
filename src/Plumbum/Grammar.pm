=begin overview

This is the grammar for Plumbum in Perl 6 rules.

=end overview

grammar Plumbum::Grammar is HLL::Grammar;

token TOP {
    <statementlist>
    [ $ || <.panic: "Syntax error"> ]
}

## Lexer items

# This <ws> rule treats # as "comment to eol".
token ws {
    <!ww>
    [ '#' \N* \n? | \s+ ]*
}

## Statements

rule statementlist { [ <statement> | <?> ] ** ';' }

rule statement {
    | <statement_control>
    | <EXPR>
}

proto token statement_control { <...> }
rule statement_control:sym<say>   { <sym> [ <EXPR> ] ** ','  }
rule statement_control:sym<print> { <sym> [ <EXPR> ] ** ','  }

## Terms

token term:sym<integer> { <integer> }
token term:sym<quote> { <quote> }

proto token quote { <...> }
token quote:sym<'> { <?[']> <quote_EXPR: ':q'> }
token quote:sym<"> { <?["]> <quote_EXPR: ':qq'> }

## Operators

INIT {
    Plumbum::Grammar.O(':prec<u>, :assoc<left>',  '%multiplicative');
    Plumbum::Grammar.O(':prec<t>, :assoc<left>',  '%additive');
}

token circumfix:sym<( )> { '(' <.ws> <EXPR> ')' }

token infix:sym<*>  { <sym> <O('%multiplicative, :pirop<mul>')> }
token infix:sym</>  { <sym> <O('%multiplicative, :pirop<div>')> }

token infix:sym<+>  { <sym> <O('%additive, :pirop<add>')> }
token infix:sym<->  { <sym> <O('%additive, :pirop<sub>')> }
