module "rds_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.3.1"

  name        = "${local.project}-rds-sg"
  description = "RDS PostgreSQL"
  vpc_id      = module.vpc.vpc_id

  ingress_with_source_security_group_id = [
    {
      rule                     = "postgresql-tcp"
      source_security_group_id = module.databricks_sg.security_group_id
    },
    {
      rule                     = "postgresql-tcp"
      source_security_group_id = module.lambda_sg.security_group_id
    }
  ]
}

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "7.2.0"

  identifier     = "${local.project}-postgres"
  engine         = "postgres"
  engine_version = "15.15"
  instance_class = "db.t4g.micro"

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"

  db_name                     = local.project
  username                    = local.db_user
  manage_master_user_password = false
  password_wo                 = var.rds_password
  password_wo_version         = 0

  create_db_subnet_group = true
  subnet_ids             = module.vpc.database_subnets
  vpc_security_group_ids = [module.rds_sg.security_group_id]

  publicly_accessible    = false
  skip_final_snapshot    = true
  apply_immediately      = true
  create_db_option_group = false

  family = "postgres15"
}
