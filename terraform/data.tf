# AWS 계정 정보
data "aws_caller_identity" "current" {}

# AWS 지역 정보
data "aws_region" "current" {}

# AWS 가용 영역 
data "aws_availability_zones" "available" {
  state = "available"
}
