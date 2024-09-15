# Use the official AWS Lambda Python 3.9 base image
FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies
# Install Poetry
RUN pip install poetry

# Copy pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock ./

# Install dependencies using Poetry without creating a virtual environment
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy your application code to the Lambda task root directory
COPY app/ ${LAMBDA_TASK_ROOT}

# Set the command to your Lambda function handler
CMD ["lambda_function.lambda_handler"]
