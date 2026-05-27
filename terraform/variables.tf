variable "databricks_account_id" {
  description = "Databricks 계정 ID"
  type        = string
}

variable "databricks_client_id" {
  description = "Databricks Service Principal Client ID"
  type        = string
}

variable "databricks_client_secret" {
  description = "Databricks Service Principal Client Secret"
  type        = string
  sensitive   = true
}

variable "databricks_username" {
  description = "Databricks 사용자 이름(이메일 주소)"
  type        = string

  validation {
    # 정규표현식을 사용하여 이메일 형식 확인
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.databricks_username))
    error_message = "유효한 이메일 주소 형식이 아닙니다. 올바른 형식을 입력해주세요. (예: admin@example.com)"
  }
}

variable "rds_password" {
  description = "RDS 마스터 비밀번호"
  type        = string
  default     = "W0rkshop!DB2026"
  sensitive   = true
}
