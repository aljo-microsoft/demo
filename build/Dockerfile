FROM golang:1.8
RUN mkdir /goapp
ADD . /goapp/
WORKDIR /goapp
RUN go build -o main .
CMD ["/goapp/main"]
