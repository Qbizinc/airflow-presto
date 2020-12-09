resource "aws_ecs_task_definition" "task-def" {
  family = "${var.BASE_NAME}-presto-definition"

  execution_role_arn       = aws_iam_role.ecs-task-role.arn
  container_definitions    = file("${path.module}/container-definition.json")
  cpu                      = 4096
  memory                   = 30720
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  tags                     = var.TAGS
}
