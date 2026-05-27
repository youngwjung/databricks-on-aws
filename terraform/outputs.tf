output "workspace_url" {
  description = "Databricks 워크스페이스 URL"
  value       = databricks_mws_workspaces.this.workspace_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL 엔드포인트"
  value       = module.rds.db_instance_address
}

output "documents_s3_uri" {
  description = "비정형 문서 S3 경로"
  value       = "s3://${module.documents_bucket.s3_bucket_id}/documents"
}

output "chat_app_url" {
  description = "CS AI 어시스턴트 채팅 앱 URL"
  value       = "https://${module.chat_cdn.cloudfront_distribution_domain_name}"
}