
# comments should be ignored
[2,3,4,1,2,5,3,2] | sort | uniq    # from '#' to eol

foo = strip | compact
<old_test.pb> | foo | grep /[aeiou]{2}/ | sort | count

lexsort = ord | sort | chr
["Hello, world!"] | split '' | flatten | lexsort | uniq | join '' | print

<old_test.pb> | strip | compact | grep /[aeiou]{2}/ | sort | count

`yes` | strip | head 10 | uniq

[[2,32],[3,2,1],[3]] | flatten |sum

[1..] | zip `yes` | flatten | head 10

`yes` | zip { [8,7..3] | sort } | count

['','',"stdlib tests passed",'',''] | print
