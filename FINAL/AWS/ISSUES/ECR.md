# [ECR Issues](https://youtu.be/GQZIuIOaZdI?si=EWsicOvQ1JclZapa)

1. Check the IAM User has proper permissions
2. Check the IAM user has following permissions "sts: GetServiceBearerToken"
3. Check whether ECR Registry private or public, we need to execute the commands accordingly
4. Check the docker images names are properly tagged
5. Try with proper access key and secret key
6. Try to update the AWS CLI version and try again pushing the image via docker

