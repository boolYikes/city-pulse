FROM public.ecr.aws/lambda/python:3.12

# The variable is implicit in aws lambda containers
# Point build context to root and explicitly set which Dockerfile to use
# otherwise COPY directive will break
COPY pyproject.toml .
COPY src/ ${LAMBDA_TASK_ROOT}/src/
COPY lambda/ ${LAMBDA_TASK_ROOT}/lambda/

RUN pip install . -t "${LAMBDA_TASK_ROOT}"

# Default. Override when provisioning using Terraform and whatnot
CMD ["lambda.extract.handler.aq_extract_handler"]
