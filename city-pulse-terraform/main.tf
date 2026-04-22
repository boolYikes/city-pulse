provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}

############################
# IAM ROLE (OPTIONAL CREATE)
############################

data "aws_iam_role" "existing_lambda_role" {
  count = var.create_lambda_role ? 0 : 1
  name  = var.existing_lambda_role_name
}

resource "aws_iam_role" "lambda_role" {
  count = var.create_lambda_role ? 1 : 0

  name = "City-Pulse-S3-Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  count = var.create_lambda_role ? 1 : 0

  name = "CityPulseS3Permissions"
  role = aws_iam_role.lambda_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:*"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

locals {
  lambda_role_arn = var.create_lambda_role
    ? aws_iam_role.lambda_role[0].arn
    : data.aws_iam_role.existing_lambda_role[0].arn
}

############################
# LAMBDA FUNCTIONS
############################

resource "aws_lambda_function" "extract" {
  function_name = "${var.project_name}-extract"
  role          = local.lambda_role_arn
  handler       = "handler.extract_handler"
  runtime       = "python3.12"

  filename         = "lambda/extract.zip"
  source_code_hash = filebase64sha256("lambda/extract.zip")

  environment {
    variables = {
      PIPELINE         = "bronze"
      OPENAQ_API_KEY   = var.openaq_api_key
      S3_REGION_NAME   = var.region
    }
  }
}

resource "aws_lambda_function" "transform" {
  function_name = "${var.project_name}-transform"
  role          = local.lambda_role_arn
  handler       = "handler.transform_handler"
  runtime       = "python3.12"

  filename         = "lambda/transform.zip"
  source_code_hash = filebase64sha256("lambda/transform.zip")

  environment {
    variables = {
      PIPELINE         = "silver"
      OPENAQ_API_KEY   = var.openaq_api_key
      S3_REGION_NAME   = var.region
    }
  }
}

############################
# STEP FUNCTIONS
############################

resource "aws_iam_role" "stepfn_role" {
  name = "${var.project_name}-stepfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "stepfn_policy" {
  role = aws_iam_role.stepfn_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["lambda:InvokeFunction"]
      Resource = [
        aws_lambda_function.extract.arn,
        aws_lambda_function.transform.arn
      ]
    }]
  })
}

resource "aws_sfn_state_machine" "etl" {
  name     = "${var.project_name}-etl"
  role_arn = aws_iam_role.stepfn_role.arn

  definition = templatefile("${path.module}/state_machine.asl.json.tftpl", {
    extract_arn   = aws_lambda_function.extract.arn
    transform_arn = aws_lambda_function.transform.arn
    bucket        = var.bucket_name
    config        = jsonencode(var.default_city_config)
  })
}

############################
# EVENTBRIDGE SCHEDULER
############################

resource "aws_iam_role" "scheduler_role" {
  name = "${var.project_name}-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_policy" {
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["states:StartExecution"]
      Resource = aws_sfn_state_machine.etl.arn
    }]
  })
}

resource "aws_scheduler_schedule" "hourly" {
  name = "${var.project_name}-hourly"

  schedule_expression = var.schedule_expression

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sfn_state_machine.etl.arn
    role_arn = aws_iam_role.scheduler_role.arn

    input = jsonencode({
      city      = var.default_city_config.city
      lat       = var.default_city_config.lat
      lon       = var.default_city_config.lon
      log_level = var.default_city_config.log_level
      rad       = var.default_city_config.rad
      BUCKET    = var.bucket_name
    })
  }
}
