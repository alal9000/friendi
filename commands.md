# DOCKER

## local

docker build --tag friendi . <!-- build docker image -->  
docker run --publish 8000:8000 friendi <!-- create/run container -->

## remote

docker login <!-- login to dockerhub -->
docker tag friendi lucidlear/friendi<:version> <!-- add new tag to existing tag, note if version is omitted it will go under the tag 'latest' -->
docker push lucidlear/friendi<:version> <!-- push image to dockerhub -->

## bulk commands

docker build --tag friendi .  
docker login
docker tag friendi lucidlear/friendi<:version>
docker push lucidlear/friendi<:version>

# GIT
