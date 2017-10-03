resource "aws_iam_user" "load_test_user" {
  name = "load_test_user-${var.key_name}"
  path = "/"
}

# TODO Restrict policy just to nessisary access
resource "aws_iam_user_policy" "load_test_user_ploicy" {
  name = "test"
  user = "${aws_iam_user.load_test_user.name}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "*",
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}

resource "aws_iam_role" "load_test_user_role" {
  name_prefix = "girder_load_test-"
  assume_role_policy =  <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {"AWS": ["${aws_iam_user.load_test_user.arn}"]},
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "load_test_user" {
  name_prefix = "item-tasks-"
  role = "${aws_iam_role.load_test_user_role.name}"
}
