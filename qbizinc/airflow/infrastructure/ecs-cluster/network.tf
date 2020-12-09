data "aws_vpc" "selected" {
  id = var.vpc_id
}

resource "aws_subnet" "cluster_subnet" {
  vpc_id            = data.aws_vpc.selected.id
  availability_zone = "us-west-2a"
  cidr_block        = cidrsubnet(data.aws_vpc.selected.cidr_block, 4, 3)
}

resource "aws_security_group" "security_group" {
  name        = var.BASE_NAME
  description = "Presto ECS Cluster security group"
  vpc_id      = var.vpc_id
  tags        = var.TAGS

  ingress {
    protocol    = "tcp"
    from_port   = 8080
    to_port     = 8080
    cidr_blocks = [aws_subnet.cluster_subnet.cidr_block]
  }
  ingress {
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = [aws_subnet.cluster_subnet.cidr_block]
  }
  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

}
