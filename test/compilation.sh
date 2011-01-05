set -e
PROGRAM='[1,5,3,7,2,4,2,1] | sort | println ","'
dashE=`../pb -e "$PROGRAM"`
echo $PROGRAM | ../pb -c ctest.pbc -
comp=`../pb ctest.pbc`
if [ $comp != $dashE ]; then
	echo "Compilation test fail"
	echo $dashE
	echo $comp
else
	echo "Compilation test success"
fi
rm -f ctest.pbc
