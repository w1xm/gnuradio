all: base gui

bokehgui_rev ?= $(word 1, $(shell git ls-remote https://github.com/w1xm/gr-bokehgui w1xm))
rci_rev ?= $(word 1, $(shell git ls-remote https://github.com/w1xm/rci_interface HEAD))

build_args = --build-arg makewidth=4 --build-arg bokehgui_rev=$(bokehgui_rev) --build-arg rci_rev=$(rci_rev)

base: Dockerfile
	docker build --target base $(build_args) -t w1xm/base .

gui: Dockerfile
	docker build --target gui $(build_args) -t w1xm/gui .
