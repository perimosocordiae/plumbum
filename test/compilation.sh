set -e
PROGRAM='[1,5,3,7,2,4,2,1] | sort | println ","'
dashE=`../cjsh -e "$PROGRAM"`
echo $PROGRAM | ../cjsh -c ctest.cjc -
comp=`../cjsh ctest.cjc`
if [ $comp != $dashE ]; then
	echo "Compilation test fail"
	echo $dashE
	echo $comp
else
	echo "Compilation test success"
fi
rm -f ctest.cjc
