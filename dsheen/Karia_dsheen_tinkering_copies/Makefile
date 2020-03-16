images := $(patsubst %.grc,%,$(wildcard *.grc))
all: image $(images)

image: Dockerfile
	docker build --build-arg makewidth=16 -t dsheen/karia_dsheen_tinkering_copies .

%: %.grc Dockerfile
	docker build --build-arg makewidth=16 --build-arg flowgraph=$< -t w1xm/dsheen/$@ .
