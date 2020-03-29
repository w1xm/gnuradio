all: base gui

base: Dockerfile
	docker build --target base --build-arg makewidth=4 -t w1xm/base .

gui: Dockerfile
	docker build --target gui --build-arg makewidth=4 -t w1xm/gui .
