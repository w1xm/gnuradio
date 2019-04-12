image: Dockerfile
	docker build  --build-arg makewidth=16 -t w1xm/ssb_transceiver .

%: %.grc
	docker build --build-arg makewidth=16 --build-arg flowgraph=$< -t w1xm/dsheen/$@ .
