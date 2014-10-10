# See XDG_DATA_HOME
LOCAL = ~/.local

BINDIR = $(LOCAL)/bin

test:
	./nag_test 2>/dev/null

install: nag test
	install -d $(BINDIR)
	install -t $(BINDIR) nag
