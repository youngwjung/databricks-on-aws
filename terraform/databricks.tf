# 자격증명 - https://docs.databricks.com/aws/en/admin/workspace/create-uc-workspace#create-a-credential-configuration
data "aws_iam_policy_document" "databricks_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::414351767826:root"]
    }
    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [var.databricks_account_id]
    }
  }
}

resource "aws_iam_role" "databricks_cross_account" {
  name               = "databricks-cross-account-role"
  assume_role_policy = data.aws_iam_policy_document.databricks_assume_role.json
}

data "aws_iam_policy_document" "databricks_cross_account" {
  statement {
    effect = "Allow"
    actions = [
      "ec2:AssociateIamInstanceProfile",
      "ec2:AttachVolume",
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:CancelSpotInstanceRequests",
      "ec2:CreateTags",
      "ec2:CreateVolume",
      "ec2:DeleteTags",
      "ec2:DeleteVolume",
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeIamInstanceProfileAssociations",
      "ec2:DescribeInstanceStatus",
      "ec2:DescribeInstances",
      "ec2:DescribeInternetGateways",
      "ec2:DescribeNatGateways",
      "ec2:DescribeNetworkAcls",
      "ec2:DescribePrefixLists",
      "ec2:DescribeReservedInstancesOfferings",
      "ec2:DescribeRouteTables",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSpotInstanceRequests",
      "ec2:DescribeSpotPriceHistory",
      "ec2:DescribeSubnets",
      "ec2:DescribeVolumes",
      "ec2:DescribeVpcAttribute",
      "ec2:DescribeVpcs",
      "ec2:DetachVolume",
      "ec2:DisassociateIamInstanceProfile",
      "ec2:ReplaceIamInstanceProfileAssociation",
      "ec2:RequestSpotInstances",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
      "ec2:RunInstances",
      "ec2:TerminateInstances",
      "ec2:DescribeFleetHistory",
      "ec2:ModifyFleet",
      "ec2:DeleteFleets",
      "ec2:DescribeFleetInstances",
      "ec2:DescribeFleets",
      "ec2:CreateFleet",
      "ec2:DeleteLaunchTemplate",
      "ec2:GetLaunchTemplateData",
      "ec2:CreateLaunchTemplate",
      "ec2:DescribeLaunchTemplates",
      "ec2:DescribeLaunchTemplateVersions",
      "ec2:ModifyLaunchTemplate",
      "ec2:DeleteLaunchTemplateVersions",
      "ec2:CreateLaunchTemplateVersion",
      "ec2:AssignPrivateIpAddresses",
      "ec2:GetSpotPlacementScores",
    ]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "iam:CreateServiceLinkedRole",
      "iam:PutRolePolicy"
    ]
    resources = [
      "arn:aws:iam::*:role/aws-service-role/spot.amazonaws.com/AWSServiceRoleForEC2Spot"
    ]
    condition {
      test     = "StringLike"
      variable = "iam:AWSServiceName"
      values   = ["spot.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy" "databricks_cross_account" {
  name   = "databricks-cross-account-policy"
  role   = aws_iam_role.databricks_cross_account.id
  policy = data.aws_iam_policy_document.databricks_cross_account.json
}

resource "databricks_mws_credentials" "this" {
  provider         = databricks.account
  credentials_name = data.aws_caller_identity.current.account_id
  role_arn         = aws_iam_role.databricks_cross_account.arn

  depends_on = [
    module.rds
  ]
}

# 네트워크 - https://docs.databricks.com/aws/en/security/network/classic/customer-managed-vpc#register-your-vpc-with-databricks
# https://docs.databricks.com/aws/en/security/network/classic/customer-managed-vpc#security-groups
module "databricks_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.3.1"

  name        = "${local.project}-databricks-sg"
  description = "Databricks cluster communication"
  vpc_id      = module.vpc.vpc_id

  ingress_with_self = [
    { rule = "all-tcp" },
    { rule = "all-udp" }
  ]

  egress_with_self = [
    { rule = "all-tcp" },
    { rule = "all-udp" }
  ]

  egress_with_cidr_blocks = [
    {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "Databricks infrastructure, cloud data sources, library repositories"
    },
    {
      from_port   = 3306
      to_port     = 3306
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "Metastore"
    },
    {
      from_port   = 6666
      to_port     = 6666
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "Secure cluster connectivity"
    },
    {
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "Lakebase"
    },
    {
      from_port   = 8443
      to_port     = 8451
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "Control plane API, Unity Catalog logging, lineage data streaming"
    },
    {
      from_port   = 53
      to_port     = 53
      protocol    = "tcp"
      cidr_blocks = "0.0.0.0/0"
      description = "DNS"
    },
    {
      from_port   = 53
      to_port     = 53
      protocol    = "udp"
      cidr_blocks = "0.0.0.0/0"
      description = "DNS"
    }
  ]
}

resource "databricks_mws_networks" "this" {
  provider           = databricks.account
  account_id         = var.databricks_account_id
  network_name       = data.aws_caller_identity.current.account_id
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [module.databricks_sg.security_group_id]
}

# 스토리지 - https://docs.databricks.com/aws/en/admin/workspace/create-uc-workspace#create-a-storage-configuration
module "databricks_bucket" {
  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "5.13.0"

  bucket_prefix = "${data.aws_caller_identity.current.account_id}-workspace-storage"
  attach_policy = false
  force_destroy = true
}

data "aws_iam_policy_document" "databricks_access" {
  statement {
    sid    = "Grant Databricks Access"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::414351767826:root"]
    }

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucketLocation"
    ]

    resources = [
      module.databricks_bucket.s3_bucket_arn,
      "${module.databricks_bucket.s3_bucket_arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:PrincipalTag/DatabricksAccountId"
      values   = [var.databricks_account_id]
    }
  }

  statement {
    sid    = "Prevent DBFS from accessing Unity Catalog metastore"
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::414351767826:root"]
    }

    actions = [
      "s3:*"
    ]

    resources = [
      "${module.databricks_bucket.s3_bucket_arn}/unity-catalog/*"
    ]
  }
}

resource "aws_s3_bucket_policy" "databricks_access" {
  bucket = module.databricks_bucket.s3_bucket_id
  policy = data.aws_iam_policy_document.databricks_access.json
}


locals {
  databricks_storage_role = "databricks-storage-role"
}

data "aws_iam_policy_document" "databricks_storage_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::414351767826:role/unity-catalog-prod-UCMasterRole-14S5ZJVKOTYTL",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [var.databricks_account_id]
    }
  }
}

resource "aws_iam_role" "databricks_storage" {
  name               = local.databricks_storage_role
  assume_role_policy = data.aws_iam_policy_document.databricks_storage_assume_role.json
}

data "aws_iam_policy_document" "databricks_storage" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:ListBucketMultipartUploads",
      "s3:ListMultipartUploadParts",
      "s3:AbortMultipartUpload"
    ]
    resources = [
      module.databricks_bucket.s3_bucket_arn,
      "${module.databricks_bucket.s3_bucket_arn}/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
    resources = [
      aws_iam_role.databricks_storage.arn
    ]
  }
}

resource "aws_iam_role_policy" "databricks_storage" {
  name   = "databricks-storage-policy"
  role   = aws_iam_role.databricks_storage.id
  policy = data.aws_iam_policy_document.databricks_storage.json
}

resource "databricks_mws_storage_configurations" "this" {
  provider                   = databricks.account
  account_id                 = var.databricks_account_id
  storage_configuration_name = data.aws_caller_identity.current.account_id
  bucket_name                = module.databricks_bucket.s3_bucket_id
  role_arn                   = aws_iam_role.databricks_storage.arn
}

# 워크스페이스 - https://docs.databricks.com/aws/en/admin/workspace/create-workspace
resource "databricks_metastore" "this" {
  provider     = databricks.account
  name         = replace(var.databricks_username, "/[^a-zA-Z0-9]/", "-")
  region       = data.aws_region.current.region
  owner        = "account users"
  storage_root = "s3://${module.databricks_bucket.s3_bucket_id}/metastore"

  force_destroy = true
}

resource "databricks_metastore_data_access" "this" {
  provider     = databricks.account
  metastore_id = databricks_metastore.this.id
  name         = "metadata-access"
  aws_iam_role {
    role_arn = aws_iam_role.databricks_storage.arn
  }
  is_default = true

  force_destroy = true
}

resource "databricks_mws_workspaces" "this" {
  provider       = databricks.account
  account_id     = var.databricks_account_id
  workspace_name = replace(var.databricks_username, "/[^a-zA-Z0-9]/", "-")
  aws_region     = data.aws_region.current.region

  credentials_id           = databricks_mws_credentials.this.credentials_id
  storage_configuration_id = databricks_mws_storage_configurations.this.storage_configuration_id
  network_id               = databricks_mws_networks.this.network_id

  depends_on = [
    databricks_metastore.this
  ]
}

resource "databricks_metastore_assignment" "this" {
  provider     = databricks.account
  metastore_id = databricks_metastore.this.id
  workspace_id = databricks_mws_workspaces.this.workspace_id
}

# 유저 - https://docs.databricks.com/aws/en/admin/users-groups/users
data "databricks_user" "this" {
  provider  = databricks.account
  user_name = var.databricks_username
}

resource "databricks_mws_permission_assignment" "this" {
  provider     = databricks.account
  workspace_id = databricks_mws_workspaces.this.workspace_id
  principal_id = data.databricks_user.this.id
  permissions  = ["ADMIN"]

  depends_on = [
    databricks_metastore_assignment.this
  ]
}

# Databricks에 S3 버킷 권한 부여 - https://docs.databricks.com/aws/en/connect/unity-catalog/cloud-storage/s3/s3-external-location-manual
data "aws_iam_policy_document" "databricks_external_storage_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::414351767826:role/unity-catalog-prod-UCMasterRole-14S5ZJVKOTYTL",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
  }
}

resource "aws_iam_role" "databricks_external_storage" {
  name               = "databricks-external-storage-role"
  assume_role_policy = data.aws_iam_policy_document.databricks_external_storage_assume_role.json
}

data "aws_iam_policy_document" "databricks_external_storage" {
  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:ListBucketMultipartUploads",
      "s3:ListMultipartUploadParts",
      "s3:AbortMultipartUpload"
    ]
    resources = [
      module.documents_bucket.s3_bucket_arn,
      "${module.documents_bucket.s3_bucket_arn}/*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
    resources = [
      aws_iam_role.databricks_external_storage.arn
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "s3:GetBucketNotification",
      "s3:PutBucketNotification",
      "sns:ListSubscriptionsByTopic",
      "sns:GetTopicAttributes",
      "sns:SetTopicAttributes",
      "sns:CreateTopic",
      "sns:TagResource",
      "sns:Publish",
      "sns:Subscribe",
      "sqs:CreateQueue",
      "sqs:DeleteMessage",
      "sqs:ReceiveMessage",
      "sqs:SendMessage",
      "sqs:GetQueueUrl",
      "sqs:GetQueueAttributes",
      "sqs:SetQueueAttributes",
      "sqs:TagQueue",
      "sqs:ChangeMessageVisibility",
      "sqs:PurgeQueue"
    ]
    resources = [
      module.documents_bucket.s3_bucket_arn,
      "arn:aws:sqs:*:*:csms-*",
      "arn:aws:sns:*:*:csms-*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "sqs:ListQueues",
      "sqs:ListQueueTags",
      "sns:ListTopics"
    ]
    resources = [
      "arn:aws:sqs:*:*:csms-*",
      "arn:aws:sns:*:*:csms-*"
    ]
  }
  statement {
    effect = "Allow"
    actions = [
      "sns:Unsubscribe",
      "sns:DeleteTopic",
      "sqs:DeleteQueue"
    ]
    resources = [
      "arn:aws:sqs:*:*:csms-*",
      "arn:aws:sns:*:*:csms-*"
    ]
  }
}

resource "aws_iam_role_policy" "databricks_external_storage" {
  name   = "databricks-external-storage-policy"
  role   = aws_iam_role.databricks_external_storage.id
  policy = data.aws_iam_policy_document.databricks_external_storage.json
}

resource "databricks_storage_credential" "databricks_external_storage" {
  provider = databricks.workspace
  name     = aws_iam_role.databricks_external_storage.name
  aws_iam_role {
    role_arn = aws_iam_role.databricks_external_storage.arn
  }

  depends_on = [
    databricks_metastore_assignment.this
  ]

  force_destroy = true
}

resource "databricks_grants" "databricks_external_storage" {
  provider           = databricks.workspace
  storage_credential = databricks_storage_credential.databricks_external_storage.id
  grant {
    principal  = var.databricks_username
    privileges = ["ALL PRIVILEGES"]
  }
}

# Databricks에 Amazon Bedrock 권한 부여
data "aws_iam_policy_document" "databricks_bedrock_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::414351767826:role/unity-catalog-prod-UCMasterRole-14S5ZJVKOTYTL",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "sts:ExternalId"
      values   = [var.databricks_account_id]
    }
  }
}

resource "aws_iam_role" "databricks_bedrock" {
  name               = "databricks-bedrock-role"
  assume_role_policy = data.aws_iam_policy_document.databricks_bedrock_assume_role.json
}

data "aws_iam_policy_document" "databricks_bedrock" {
  statement {
    effect = "Allow"
    actions = [
      "sts:AssumeRole"
    ]
    resources = [
      aws_iam_role.databricks_bedrock.arn
    ]
  }
}

resource "aws_iam_role_policy" "databricks_bedrock" {
  name   = "databricks-bedrock-policy"
  role   = aws_iam_role.databricks_bedrock.id
  policy = data.aws_iam_policy_document.databricks_bedrock.json
}

resource "aws_iam_role_policy_attachment" "databricks_bedrock_role_bedrock_rw" {
  role       = aws_iam_role.databricks_bedrock.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

resource "databricks_credential" "bedrock" {
  provider = databricks.workspace
  name     = aws_iam_role.databricks_bedrock.name
  aws_iam_role {
    role_arn = aws_iam_role.databricks_bedrock.arn
  }
  purpose = "SERVICE"

  depends_on = [
    databricks_metastore_assignment.this
  ]
}

resource "databricks_grants" "databricks_bedrock" {
  provider   = databricks.workspace
  credential = databricks_credential.bedrock.id
  grant {
    principal  = var.databricks_username
    privileges = ["ALL PRIVILEGES"]
  }
}