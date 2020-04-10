all: image headless

image: Dockerfile
	docker build --target qradiolink -t w1xm/qradiolink .
headless: Dockerfile image
	docker build --target headless -t w1xm/qradiolink/headless .
