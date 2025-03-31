# DOCKER

## local

docker build --tag friendi . <!-- build docker image -->  
docker run --publish 8000:8000 friendi <!-- create/run container -->

## remote

docker login <!-- login to dockerhub -->
docker tag friendi lucidlear/friendi <!-- add new tag to existing tag -->
docker push lucidlear/friendi <!-- push image to dockerhub -->

## bulk commands

docker build --tag friendi .  
docker login
docker tag friendi lucidlear/friendi
docker push lucidlear/friendi

# GIT
