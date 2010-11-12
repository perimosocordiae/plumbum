
# comments should be ignored
[2,3,4,1,2,5,3,2] | sort | inc    # from '#' to eol

# assignment is currently broken, with the new AST
#foo = strip | compact
#<stdlib.cj> | $foo | grep /[aeiou]{2}/ | sort | count

<stdlib.cj> | strip | compact | grep /[aeiou]{2}/ | sort | count

`yes` | strip | head 10| uniq

[[2,32],3,2,[3,[[3]]]] | flatten |sum

range 100000000000 | zip `yes` | flatten | head 10

`yes` | zip ^range 5^ | count

"\n\nstdlib tests passed\n\n" | println
