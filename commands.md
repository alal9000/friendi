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

==================================================================

# Start here

## steps to push new image to dh(app):

1. build the image locally under the 'friendi' image -> docker build -f Dockerfile.web -t friendi .
2. login to dockerhub -> docker login
3. map the local friendi image to a dockerhub image and tag to push to remote -> docker tag friendi lucidlear/friendi<:version>
4. push our new remote image to docker hub -> docker push lucidlear/friendi<:version>

## steps to push new image to dh: (worker)

1. build the image locally under the 'friendi-worker' image from the worker Dockerfile -> docker build -f Dockerfile.worker -t friendi-worker .
2. login to dockerhub -> docker login
3. map the local friendi-worker image to a dockerhub image and tag to push to remote -> docker tag friendi-worker lucidlear/friendi:worker
4. push our new remote image to docker hub -> docker push lucidlear/friendi:worker
