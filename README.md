# Plumbum #

An experimental, pipe-oriented programming language, designed to fill the
gap between classic Unix shell one-liners and powerful general-purpose
programming languages.

## Dependencies ##
 * Python 2.x (probably 2.6+, though I haven't tested earlier versions)
 * Some modern Linux or Mac OS X

## Usage ##
<table>
<tr><td>Start up a REPL</td><td><pre>./pb</pre></td></tr>
<tr><td>Eval one line</td><td><pre>./pb -e '["hello","world"] " " join println'</pre></td></tr>
<tr><td>Run a program</td><td><pre>./pb -f foo.pb</pre></td></tr>
</table>

## Code Examples ##
Some 'real' code examples:

    # should be self-explanatory
    "hello, world!\n" print

    # list literals
    [2,4,1,4,2] uniq
	
    # lazy range literals (ala Haskell)
    [4..] zip [10,9..1] flatten

    # slurping a file, perl-ish regexen
    <foo.txt> /bar/ grep println

    # inline (lazy!) shell commands
    `yes` strip 10 take "," join print

    # name a pipeline, use it later
    uniq sort = foo
    # slurp from standard in
    <> foo println

