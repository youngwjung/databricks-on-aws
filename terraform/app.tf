data "aws_ec2_managed_prefix_list" "cloudfront" {
  name = "com.amazonaws.global.cloudfront.origin-facing"
}

data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer" {
  name = "Managed-AllViewer"
}

module "chat_alb_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.3.1"

  name        = "${local.project}-chat-alb-sg"
  description = "Chat app ALB"
  vpc_id      = module.vpc.vpc_id

  ingress_with_prefix_list_ids = [
    {
      rule            = "http-80-tcp"
      prefix_list_ids = data.aws_ec2_managed_prefix_list.cloudfront.id
    }
  ]
  egress_rules = ["all-all"]
}

module "chat_ecs_sg" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "5.3.1"

  name        = "${local.project}-chat-ecs-sg"
  description = "Chat app ECS"
  vpc_id      = module.vpc.vpc_id

  ingress_with_source_security_group_id = [
    {
      from_port                = 8501
      to_port                  = 8501
      protocol                 = "tcp"
      source_security_group_id = module.chat_alb_sg.security_group_id
    }
  ]
  egress_rules = ["all-all"]
}

module "chat_alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "10.5.0"

  name               = "${local.project}-chat-alb"
  load_balancer_type = "application"
  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets

  create_security_group = false
  security_groups       = [module.chat_alb_sg.security_group_id]

  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"
      forward = {
        target_group_key = "chat"
      }
    }
  }

  target_groups = {
    chat = {
      protocol          = "HTTP"
      port              = 8501
      target_type       = "ip"
      create_attachment = false

      health_check = {
        enabled             = true
        path                = "/healthz"
        healthy_threshold   = 2
        unhealthy_threshold = 3
      }
    }
  }

  enable_deletion_protection = false
}

module "chat_ecs" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "7.5.0"

  cluster_name = "${local.project}-chat"

  cluster_capacity_providers = ["FARGATE"]
}

module "chat_service" {
  source  = "terraform-aws-modules/ecs/aws//modules/service"
  version = "7.5.0"

  name        = "chat"
  cluster_arn = module.chat_ecs.cluster_arn

  cpu    = 256
  memory = 512

  container_definitions = {
    chat = {
      essential = true
      image     = "youngwjung/streamlit-databricks-agent"
      portMappings = [{
        containerPort = 8501
        protocol      = "tcp"
      }]
    }
  }

  subnet_ids            = module.vpc.private_subnets
  create_security_group = false
  security_group_ids    = [module.chat_ecs_sg.security_group_id]

  load_balancer = {
    service = {
      target_group_arn = module.chat_alb.target_groups["chat"].arn
      container_name   = "chat"
      container_port   = 8501
    }
  }
}

module "chat_cdn" {
  source  = "terraform-aws-modules/cloudfront/aws"
  version = "6.7.0"

  comment = "${local.project} chat app"
  enabled = true

  origin = {
    alb = {
      domain_name = module.chat_alb.dns_name
      custom_origin_config = {
        http_port                = 80
        https_port               = 443
        origin_protocol_policy   = "http-only"
        origin_ssl_protocols     = ["TLSv1.2"]
        origin_read_timeout      = 60
        origin_keepalive_timeout = 60
      }
    }
  }

  default_cache_behavior = {
    target_origin_id         = "alb"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer.id
  }

  viewer_certificate = {
    cloudfront_default_certificate = true
    minimum_protocol_version       = "TLSv1"
  }
}