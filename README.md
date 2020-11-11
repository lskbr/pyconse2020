# pyconse2020
Code used in the PyConSE 2020 workshop: Python Serverless Microservices

This code contains 3 examples of Lambda functions use to deploy simple services.

hello.py: stub application that shows all heads in json format.

showip.py: displays user's ip and country.

urlshortner.py: a simple service to create short codes for URLs and to count how many times a url was accessed.

## Requirements:
1. Install nodejs in your system.
1. Create a new Python environment with Python 3.8.

## Installation
```
pip install -r requirements.txt awscli
npm -g serverless
sls plugin install -n serverless-python-requirements
```

## Deployment

1. Setup your AWS credentials
1. And then:
```
sls deploy
```
