
# CJSH #

Watch this space for pertinent info.

## Dependencies ##
 * Some flavor of Linux
   * currently tested on Ubuntu 10.04
 * Python 3.x

## Usage ##
 * Start up a REPL: `./cjsh`
 * Eval one line: `./cjsh -e '"hello world" | println'`
 * Run a program: `./cjsh foo.cj`
 * Compile a program: `./cjsh -c foo.cjc foo.cj`
 * Run a compiled program: `./cjsh foo.cjc`

## Code Examples ##
Some 'real' code examples:

    # should be self-explanatory
    "hello, world!" | println

    # list literals
    [2,4,1,4,2] | uniq | println

    # slurping a file, perl-ish regexen
    <foo.txt> | grep /bar/ | print

    # inline shell commands
    `yes` | strip | head 10 | println ","

    # name a pipeline, use it later
    foo = uniq | sort
    <> | foo | print
