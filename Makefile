tbxi: scripts/bootmake.py trampoline.elf parcels
	./scripts/bootmake.py $@ trampoline.elf parcels
	SetFile -t tbxi -c chrp $@ || true # macOS only

# Tomfoolery required to be able to put prclmake.py args in another file
parcels: scripts/prclmake.py scripts/prcltool.py parcel-layout.txt scripts/lzss rom $(shell find pef -type f -not -path '*/\.*')
	sh -c "scripts/prclmake.py $@ `sed 's/#.*//' parcel-layout.txt | tr '\n' ' '`"

scripts/lzss: lzss.c
	gcc -O2 -o $@ $<

clean:
	rm -rf parcels tbxi scripts/lzss scripts/__pycache__ *.hqx
	find . -type f -name '*.patch' -delete

# For your convenience (macOS only)

%.hqx: % scripts/binhexmake.py
	scripts/binhexmake.py --data=$< --type=tbxi --creator=chrp --name="Mac OS ROM" $@
