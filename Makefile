# See XDG_DATA_HOME
LOCAL = ~/.local

BINDIR = $(LOCAL)/bin

install: nag
	install -t $(BINDIR) nag
