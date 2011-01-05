
# Plumbum #

An experimental, pipe-oriented programming language, designed to fill the
gap between classic Unix shell one-liners and powerful general-purpose
programming languages.

## Dependencies ##
 * Some flavor of Linux
   * definitely works on recent Ubuntus
 * Python 3.x
 * PyParsing

## Usage ##
 * Start up a REPL: `./pb`
 * Eval one line: `./pb -e '"hello world" | println'`
 * Run a program: `./pb foo.cj`
 * Compile a program: `./pb -c foo.cjc foo.cj`
 * Run a compiled program: `./pb foo.cjc`

## Code Examples ##
Some 'real' code examples:

    # should be self-explanatory
    "hello, world!" | println

    # list literals
    [2,4,1,4,2] | uniq | println

    # slurping a file, perl-ish regexen
    <foo.txt> | grep /bar/ | print

    # inline (lazy!) shell commands
    `yes` | strip | head 10 | println ","

    # name a pipeline, use it later
    foo = uniq | sort
	# slurp from standard in
    <> | $foo | print

For more examples, see the files in the `test` directory.
