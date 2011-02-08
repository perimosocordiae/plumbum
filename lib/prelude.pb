
# Plumbum in Plumbum!
# A prelude

fst = select 1
snd = select 2

first = take 1
last = reverse | take 1
min = sort | first
max = sort | last

shuffle = zip {[1..] | rand} | flip | sort | snd

