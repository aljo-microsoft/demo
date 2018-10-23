FROM java:8
EXPOSE 8082
ADD /target/javaservice-0.0.1.jar javaservice-0.0.1.jar
ENTRYPOINT ["java", "-jar", "javaservice-0.0.1.jar", "-server.port=8082"]
