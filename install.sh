
set +e
python3 -V 2>/dev/null
if [ $? == 1 ]; then
	set -e
	echo "Installing python3 from apt-get..."
	sudo apt-get -qq install python3
fi

set +e
python3 -c 'import pyparsing' 2>/dev/null
if [ $? == 1 ]; then
	set -e
	echo "Installing pyparsing"
	PPDIR='pyparsing-1.5.5'
	curl "http://pypi.python.org/packages/source/p/pyparsing/$PPDIR.tar.gz" | tar -xzf -
	pushd $PPDIR
	sudo python3 setup.py install
	popd
	sudo rm -rf $PPDIR
fi

set -e
if [ ! -f pb ]; then
	ln -s lib/plumbum.py pb
fi

pushd test
../pb stdlib.pb
popd

echo "All systems go!"
