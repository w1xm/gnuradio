all: image

revision ?= $(word 1, $(shell git ls-remote https://github.com/w1xm/shinysdr HEAD))

image: Dockerfile
	docker build --build-arg makewidth=16 --build-arg revision=$(revision) -t w1xm/shinysdr .
