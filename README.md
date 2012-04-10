# Plumbum #

An experimental, pipe-oriented programming language, designed to fill the
gap between classic Unix shell one-liners and powerful general-purpose
programming languages.

## Dependencies ##
 * Python 2.x (probably 2.6+, though I haven't tested earlier versions)
 * PyParsing (`pip install pyparsing` or equivalent)
 * Some modern Linux or Mac OS X

## Usage ##
<table>
<tr><td>Start up a REPL</td><td><pre>./pb.py</pre></td></tr>
<tr><td>Eval one line</td><td><pre>./pb.py -e '["hello","world"] | join " " | print'</pre></td></tr>
<tr><td>Run a program</td><td><pre>./pb.py foo.pb</pre></td></tr>
</table>

## Code Examples ##
Some 'real' code examples:

    # should be self-explanatory
    ["hello, world!"] | print

    # list literals
    [2,4,1,4,2] | uniq
	
    # lazy range literals (ala Haskell)
    [4..] | zip [10,9..1] | flatten

    # slurping a file, perl-ish regexen
    <foo.txt> | grep /bar/ | print

    # inline (lazy!) shell commands
    `yes` | strip | take 10 | join "," | print

    # name a pipeline, use it later
    foo = uniq | sort
    # slurp from standard in
    <> | foo | print

For more examples, see the cases in `run_tests.py` or the `old_test.pb` file.
[This presentation](https://docs.google.com/present/edit?id=0AZnyju28KE7IZGNzNmNua3ZfMTMwZGs1MzhyYzc&hl=en&authkey=CJHUzNAD)
is slightly out of date, but it should be mostly accurate in describing the language.

