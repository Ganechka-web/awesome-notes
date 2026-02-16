# up the testing docker-compose project
echo "Starting docker compose testing project..."
docker compose -f docker-compose.test.yml up --build -d

# testing services
echo "Testing auth_service..."
docker compose -f docker-compose.test.yml exec auth-service-http-test pytest 
if [ $(docker compose -f docker-compose.test.yml logs auth-service-http-test | grep "failed|error" | wc -l ) -gt 0 ];
then
    echo "Something went wrong while testing auth_service"
    exit 1
fi

echo "Testing user_service..."
docker compose -f docker-compose.test.yml exec user-service-http-test pytest 
if [ $(docker compose -f docker-compose.test.yml logs user-service-http-test | grep "failed|error" | wc -l ) -gt 0 ];
then
    echo "Something went wrong while testing user_service"
    exit 1
fi

echo "Testing notes_service..."
docker compose -f docker-compose.test.yml exec notes-service-http-test pytest 
if [ $(docker compose -f docker-compose.test.yml logs notes-service-http-test | grep "failed|error" | wc -l ) -gt 0 ];
then
    echo "Something went wrong while testing notes_service"
    exit 1
fi

# cleanup resources
echo "Cleanup resources..."
docker compose -f docker-compose.test.yml down

if [ $(docker container ls --all | grep "testcontainers" | wc -l) -gt 0 ];
then
    docker container stop $(docker container ls --all -q --filter name="testcontainers")
fi