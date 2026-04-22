variable "region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "city-pulse"
}

variable "bucket_name" {
  default = "city-pulse-prod-us-east-1"
}

variable "create_lambda_role" {
  description = "Create IAM role or use existing"
  default     = false
}

variable "existing_lambda_role_name" {
  default = "City-Pulse-S3-Role"
}

variable "schedule_expression" {
  default = "rate(1 hour)"
}

variable "openaq_api_key" {
  type      = string
  sensitive = true
}

# Initial config (you can later override per execution)
variable "default_city_config" {
  default = {
    city      = "NewYork"
    lat       = 40.7698
    lon       = -73.9748
    log_level = "INFO"
    rad       = 12000
  }
}
