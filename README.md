# FastAPI

Simple API in python using the FastAPI framework with component tests


## Installation

- Create a virtual environment
- Activate the venv
- Install the requirements

## Usage: 

- Create an ".env" file from ".env.example"
- Fill in the vars with the proper values (examples are given
- Launch the rest server:


    $ uvicorn mediaapi.main:app


## Tests:
    
    $ python -m pytest


## OpenAPI specification

- Launch the server
- Browse to http://127.0.0.1:8000/docs
- or http://127.0.0.1:8000/redoc