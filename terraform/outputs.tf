output "workspace_url" {
  description = "Databricks 워크스페이스 URL"
  value       = databricks_mws_workspaces.this.workspace_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL 엔드포인트"
  value       = module.rds.db_instance_address
}

output "documents_bucket" {
  description = "비정형 문서 S3 버킷"
  value       = module.documents_bucket.s3_bucket_id
}