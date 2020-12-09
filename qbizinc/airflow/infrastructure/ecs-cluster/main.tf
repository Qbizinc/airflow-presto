terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 2.70"
    }
  }
}

provider "aws" {
  profile = "qbiz"
  region  = "us-west-2"
}

resource "aws_ecr_repository" "presto_repo" {
  name = var.ECR_NAME
  tags = var.TAGS
}

resource "aws_ecs_cluster" "presto_cluster" {
  name = var.ECS_NAME
  tags = var.TAGS
}

data "aws_iam_policy_document" "task-assume-role-policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs-task-role" {
  name               = "PrestoClusterTaskRole"
  description        = "Role used by Presto containers running in and ECS cluster."
  assume_role_policy = data.aws_iam_policy_document.task-assume-role-policy.json
  tags               = var.TAGS
}

data "aws_iam_policy" "glue" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

data "aws_iam_policy" "s3" {
  arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "attached_glue_policy" {
  role       = aws_iam_role.ecs-task-role.name
  policy_arn = data.aws_iam_policy.glue.arn
}
resource "aws_iam_role_policy_attachment" "attached_s3_policy" {
  role       = aws_iam_role.ecs-task-role.name
  policy_arn = data.aws_iam_policy.s3.arn
}
