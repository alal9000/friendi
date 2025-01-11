# DOCKER

## local
docker build --tag socializer . <!-- build docker image -->   
docker run --publish 8000:8000 socializer <!-- create/run container --> 

## remote
docker login <!-- login to dockerhub -->
docker tag socializer lucidlear/socializer <!-- add new tag to existing tag -->
docker push lucidlear/socializer <!-- push image to dockerhub -->

## bulk commands

docker build --tag friendi .  
docker login 
docker tag friendi lucidlear/friendi 
docker push lucidlear/friendi

# GIT
