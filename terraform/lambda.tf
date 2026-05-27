module "lambda_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.3.1"

  name        = "${local.project}-lambda-sg"
  description = "Lambda to RDS access"
  vpc_id      = module.vpc.vpc_id

  egress_rules = ["all-all"]
}

resource "aws_lambda_layer_version" "psycopg2" {
  layer_name = "psycopg2-py312"
  filename   = "${path.module}/lambda/psycopg2-py312.zip"

  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${path.module}/lambda/psycopg2-py312.zip")
}

module "rds_loader" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "8.8.0"

  function_name = "${local.project}-rds-loader"
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 60
  memory_size   = 256

  source_path = "${path.module}/lambda"

  vpc_subnet_ids         = module.vpc.private_subnets
  vpc_security_group_ids = [module.lambda_sg.security_group_id]

  environment_variables = {
    DB_HOST     = module.rds.db_instance_address
    DB_PORT     = "5432"
    DB_NAME     = local.project
    DB_USER     = local.db_user
    DB_PASSWORD = var.rds_password
    S3_BUCKET   = module.documents_bucket.s3_bucket_id
    S3_KEY      = aws_s3_object.seed_data_sql.key
  }

  layers = [
    aws_lambda_layer_version.psycopg2.arn
  ]

  attach_network_policy    = true
  attach_policy_statements = true
  policy_statements = {
    s3_read = {
      effect    = "Allow"
      actions   = ["s3:GetObject"]
      resources = ["${module.documents_bucket.s3_bucket_arn}/sql/*"]
    }
  }
}

resource "aws_lambda_invocation" "load_data" {
  function_name = module.rds_loader.lambda_function_name
  input         = jsonencode({ action = "load" })
  depends_on    = [module.rds_loader]
}
