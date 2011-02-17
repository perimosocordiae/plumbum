
build:
	parrot setup.pir

.PHONY: clean

clean:
	rm -f installable_plumbum plumbum.c	plumbum.o plumbum.pbc src/gen_*.pir
