
# comments should be ignored
[2,3,4,1,2,5,3,2] | sort | inc    # from '#' to eol

foo = strip | compact

<stdlib.cj> | foo | grep /[aeiou]{2}/ | sort | count

`yes` | strip | head 10| uniq

[[2,32],3,2,[3,[[3]]]] | flatten |sum

yes = `yes` | strip
range 100000000000 | zip $yes | flatten | head 10

"stdlib tests passed" | println
