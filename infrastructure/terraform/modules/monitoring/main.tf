# CloudWatch Log Group: API
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/civiclens-api-${var.environment}"
  retention_in_days = var.environment == "production" ? 90 : 14

  tags = {
    Name = "civiclens-api-logs-${var.environment}"
  }
}

# CloudWatch Log Group: Worker
resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/civiclens-worker-${var.environment}"
  retention_in_days = var.environment == "production" ? 90 : 14

  tags = {
    Name = "civiclens-worker-logs-${var.environment}"
  }
}

# CloudWatch Alarm: High 5xx Rate
resource "aws_cloudwatch_metric_alarm" "high_5xx" {
  count               = var.alb_arn_suffix != "" ? 1 : 0
  alarm_name          = "civiclens-high-5xx-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Triggered when ALB returns more than 10 5XX errors in 2 consecutive minutes"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }
}
