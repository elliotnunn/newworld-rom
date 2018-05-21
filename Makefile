tbxi tbxi.hqx: scripts/bootmake.py trampoline.elf parcels
	rm -f tbxi # in case of stray resource fork
	./scripts/bootmake.py tbxi trampoline.elf parcels
	SetFile -t tbxi -c chrp tbxi || true # try to set finfo on macOS

	# cd ../enablifier && ./enablify templates/mac-os-rom-9.6.1 "$(CURDIR)/tbxi" # Uncomment to use https://github.com/elliotnunn/enablifier (requires macOS)

	rm -f rsrcfork && touch rsrcfork && cp tbxi/..namedfork/rsrc rsrcfork 2>/dev/null || true # try to preserve rsrc fork before binhexing
	scripts/binhexmake.py --data=tbxi --rsrc=rsrcfork --type=tbxi --creator=chrp --name="Mac OS ROM" tbxi.hqx
	rm -f rsrcfork

# Tomfoolery required to be able to put prclmake.py args in another file
parcels: scripts/prclmake.py scripts/prcltool.py parcel-layout.txt scripts/lzss rom $(shell find pef -type f -not -path '*/\.*')
	sh -c "scripts/prclmake.py $@ `sed 's/#.*//' parcel-layout.txt | tr '\n' ' '`"

# Uncomment this block to use https://github.com/elliotnunn/powermac-rom
# rom: phonyrom
# .PHONY: phonyrom
# phonyrom:
# 	@echo "> Diving into powermac-rom repo"
# 	@cd ../powermac-rom && ./EasyBuild.sh && cp BuildResults/PowerROM "$(CURDIR)/rom-new"
# 	@cmp -s rom-new rom || mv rom-new rom
# 	@rm -f rom-new
# 	@echo "< Done with powermac-rom repo"

scripts/lzss: lzss.c
	gcc -O2 -o $@ $<

clean:
	rm -rf tbxi tbxi.hqx rsrcfork parcels scripts/lzss scripts/__pycache__
	find . -type f -name '*.patch' -delete


# For testing

REMOTE_DISK_NAME = Alpha
REMOTE_MACHINE = elliotnunn@Tigerbook.local

test-qemu: tbxi.hqx
	$(HOME)/qemu/qemu-with-tbxi.sh $<

test-fw: tbxi.hqx
	until mount | grep -q "/Volumes/$(REMOTE_DISK_NAME)"; do sleep 0.2; done \
	# START THE TEST MACHINE IN TARGET DISK MODE
	rm -f "/Volumes/$(REMOTE_DISK_NAME)/System Folder/Mac OS ROM"
	binhex -o "/Volumes/$(REMOTE_DISK_NAME)/System Folder/Mac OS ROM" $<
	diskutil unmountDisk force /dev/`diskutil info /Volumes/Alpha/ | grep "Part of Whole" | sed 's/.*:\s*//'`
	tput bel && say "ROM copied."

test-netfw: tbxi.hqx
	scp -q tbxi.hqx $(REMOTE_MACHINE):/tmp/tbxi.hqx
	ssh $(REMOTE_MACHINE) '\
	until ls "/Volumes/$(REMOTE_DISK_NAME)/System Folder" >/dev/null 2>/dev/null; \
	do sleep 0.15; \
	done; \
	rm -f "/Volumes/$(REMOTE_DISK_NAME)/System Folder/Mac OS ROM" && \
	/usr/local/bin/unar -force-overwrite -output-directory "/Volumes/$(REMOTE_DISK_NAME)/System Folder" /tmp/tbxi.hqx && \
	diskutil unmountDisk force "/Volumes/$(REMOTE_DISK_NAME)" \
	' # START THE TEST MACHINE IN TARGET DISK MODE
	tput bel && say "ROM copied."
