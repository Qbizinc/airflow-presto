variable "BASE_NAME" {
  type    = string
  default = "qbizinc"
}

variable "ECR_NAME" {
  type    = string
  default = "soren-presto-cluster"
}

variable "ECS_NAME" {
  type    = string
  default = "soren-presto-cluster"
}

variable "TAGS" {
  type = map(any)
}

variable "vpc_id" {
  type        = string
  default     = "vpc-03c49166"
  description = "VPC to create compute resources"
}
