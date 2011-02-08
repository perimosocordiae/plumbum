# Plumbum #

An experimental, pipe-oriented programming language, designed to fill the
gap between classic Unix shell one-liners and powerful general-purpose
programming languages.

## Dependencies ##
 * Python 3.x
 * PyParsing 1.5.5+
 * Some flavor of Linux

On a recent Ubuntu machine, running `./install.sh` should take care of
everything for you.

## Usage ##
<table>
<tr><td>Start up a REPL</td><td><pre>./pb</pre></td></tr>
<tr><td>Eval one line</td><td><pre>./pb -e '"hello world" | println'</pre></td></tr>
<tr><td>Run a program</td><td><pre>./pb foo.pb</pre></td></tr>
<tr><td>Compile a program</td><td><pre>./pb -c foo.pbc foo.pb</pre></td></tr>
<tr><td>Run a compiled program</td><td><pre>./pb foo.pbc</pre></td></tr>
</table>

## Code Examples ##
Some 'real' code examples:

    # should be self-explanatory
    "hello, world!" | println

    # list literals
    [2,4,1,4,2] | uniq
	
	# lazy range literals (ala Haskell)
	[4..] | zip [10,9..1] | flatten

    # slurping a file, perl-ish regexen
    <foo.txt> | grep /bar/ | print

    # inline (lazy!) shell commands
    `yes` | strip | take 10 | println ","

    # name a pipeline, use it later
    foo = uniq | sort
	# slurp from standard in
    <> | foo | print

For more examples, see the files in the `test` directory or [this presentation](https://docs.google.com/present/edit?id=0AZnyju28KE7IZGNzNmNua3ZfMTMwZGs1MzhyYzc&hl=en&authkey=CJHUzNAD).

