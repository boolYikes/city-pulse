output "state_machine_arn" {
  value = aws_sfn_state_machine.etl.arn
}

output "extract_lambda" {
  value = aws_lambda_function.extract.function_name
}

output "transform_lambda" {
  value = aws_lambda_function.transform.function_name
}
