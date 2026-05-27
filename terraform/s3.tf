module "documents_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "5.13.0"

  bucket_prefix = "${local.project}-documents-"
  force_destroy = true
}

locals {
  s3_documents = {
    "refund-policy"   = "documents/refund-policy.md"
    "shipping-guide"  = "documents/shipping-guide.md"
    "promotion-terms" = "documents/promotion-terms.md"
    "cs-manual"       = "documents/cs-manual.md"
  }
}

resource "aws_s3_object" "documents" {
  for_each = local.s3_documents
  bucket   = module.documents_bucket.s3_bucket_id
  key      = each.value
  source   = "${path.module}/../data/${each.value}"
  etag     = filemd5("${path.module}/../data/${each.value}")
}

resource "aws_s3_object" "seed_data_sql" {
  bucket = module.documents_bucket.s3_bucket_id
  key    = "sql/seed_data.sql"
  source = "${path.module}/../data/sql/seed_data.sql"
  etag   = filemd5("${path.module}/../data/sql/seed_data.sql")
}
