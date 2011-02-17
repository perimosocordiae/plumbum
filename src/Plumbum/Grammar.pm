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

rule statementlist { [ <statement> ] ** "\n" }

rule statement { <assignment> | <p_expr> }

rule assignment {
	<identifier> '=' <p_expr>
}

token identifier { <ident> }

## pipe expressions

rule p_expr { [ <atom> ] ** "|" }

rule atom { <slurp> | <shell> | <listliteral> | <string> | <fcall> }

#TODO: ranges, regexen
#TODO: don't use EXPR, it's too general
rule listliteral { '[' [ <EXPR> ] ** "," ']' }
rule string { <quote> }

token slurp { <?[<>]> <quote_EXPR: ':qq'> }
token shell { <?[`]> <quote_EXPR: ':qq'> }
rule fcall { <identifier> [[ <EXPR> ] ** \s+]* }

## Terms

token term:sym<identifier> { <identifier> }
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
