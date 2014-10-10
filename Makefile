# See XDG_DATA_HOME
LOCAL = ~/.local

BINDIR = $(LOCAL)/bin

test:
	./nag_test

install: nag.py test
	install -d $(BINDIR)
	install -T nag.py $(BINDIR)/nag
