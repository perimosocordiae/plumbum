
# pipe joiner -> joined
join = repeat | interleave | cat

# pipe -> ()
println = join "\n" | print

# () -> ()
newline = "\n" | print
