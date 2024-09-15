# Health Stuff

## Docker

### Local
Build: 
```commandline
docker build -t health-metrics .
```

Run:
```commandline
docker run -p 9000:8080 my-lambda-function
```

Test:
```commandline
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

Setting Env vars in the dockerfile:
```dockerfile
ENV MY_VARIABLE=value
```

### Push Image

Authenticate:
```commandline
aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-account-id.dkr.ecr.your-region.amazonaws.com
```

Tag:
```commandline
docker tag my-lambda-function:latest your-account-id.dkr.ecr.your-region.amazonaws.com/my-lambda-function:latest
```

Push:
```commandline
docker push your-account-id.dkr.ecr.your-region.amazonaws.com/my-lambda-function:latest
```
