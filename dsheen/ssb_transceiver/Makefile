images := $(patsubst %.grc,%,$(wildcard *.grc))
all: image $(images)

image: Dockerfile
	docker build --build-arg makewidth=16 -t w1xm/ssb_transceiver .

%: %.grc Dockerfile
	docker build --build-arg makewidth=16 --build-arg flowgraph=$< -t w1xm/dsheen/$@ .
