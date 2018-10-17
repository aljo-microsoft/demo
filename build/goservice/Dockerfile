FROM ubuntu:16.04

RUN apt-get update -y -q && apt-get upgrade -y -q

RUN apt-get install -y -q curl
RUN curl -O https://storage.googleapis.com/golang/go1.11.1.linux-amd64.tar.gz
RUN tar -xvf go1.11.1.linux-amd64.tar.gz
 
ENV PATH $PATH:/go/bin
ENV GOROOT /go
ENV PATH $PATH:$GOROOT/bin
ENV GOPATH /root/go
ENV PATH $PATH:$GOPATH

# Install goservice Dependencies, build, and run
EXPOSE 80
RUN mkdir -p $GOPATH/src/goservice
WORKDIR $GOPATH/src/goservice
ADD . .
RUN	apt-get install -y -q git-all && \
	go get -d -v github.com/gorilla/mux && \
	go get -d -v gopkg.in/mgo.v2/bson && \
	go get -d -v gopkg.in/mgo.v2 && \
	go build -o ./main.exe ./main.go

CMD ["./main.exe"]
