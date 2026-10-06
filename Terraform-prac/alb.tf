# Application Load Balancer
#
# An ALB accepts HTTP on port 80 and forwards it to the Fargate task IP on
# port 8000. Fargate tasks use awsvpc networking, so the target group type
# is "ip" rather than "instance". There is no EC2 instance to register.
#
# HTTPS needs an ACM certificate, and a public certificate needs a domain
# you control. This practice stack stays on HTTP so it can be applied
# without buying a domain. When you have a domain, add an HTTPS listener
# and redirect port 80 to it.

resource "aws_lb" "this" {
  name                       = "${local.name}-alb"
  load_balancer_type         = "application"
  internal                   = false
  security_groups            = [aws_security_group.alb.id]
  subnets                    = aws_subnet.public[*].id
  drop_invalid_header_fields = true
  enable_deletion_protection = false

  tags = {
    Name = "${local.name}-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name        = "${local.name}-tg"
  port        = var.container_port
  protocol    = "HTTP"
  vpc_id      = aws_vpc.this.id
  target_type = "ip"

  deregistration_delay = 30

  health_check {
    # Django admin login returns 200 without a session.
    # The site root can redirect, and the default ALB matcher only accepts 200.
    path                = "/admin/login/"
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 5
  }

  tags = {
    Name = "${local.name}-tg"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
