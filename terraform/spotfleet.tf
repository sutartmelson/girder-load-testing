variable "spot_num" {
  type = "string"
}

variable "spot_bid" {
  type = "string"
}

variable "spot_instance_type" {
  type= "string"
  default = "m4.large"
}

resource "aws_iam_policy_attachment" "fleet" {
  name       = "girder-load-test-fleet"
  roles      = ["${aws_iam_role.fleet.name}"]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2SpotFleetRole"
}

resource "aws_iam_role" "fleet" {
  name_prefix = "girder-load-test-fleet-"

  assume_role_policy = <<EOF
{
  "Version": "2008-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "spotfleet.amazonaws.com",
          "ec2.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_spot_fleet_request" "locust_slaves" {
  iam_fleet_role                      = "${aws_iam_role.fleet.arn}"
  spot_price                          = "${var.spot_bid}"
  target_capacity                     = "${var.spot_num}"
  replace_unhealthy_instances         = true
  terminate_instances_with_expiration = true

  launch_specification {
    ami                    = "${data.aws_ami.locust_ami.image_id}"
    instance_type          = "${var.spot_instance_type}"
    availability_zone      = "${var.zone}"
    key_name               = "${var.key_name}"
    iam_instance_profile   = "${aws_iam_instance_profile.load_test_user.id}"
    vpc_security_group_ids = ["${aws_security_group.basic.id}"]
    subnet_id              = "${aws_subnet.default.id}"
    user_data = <<EOF
#!/bin/bash
echo "GIRDER_HOST_URL=http://${var.girder_private_ip}:8080" > /etc/default/locust
echo "LOCUST_MASTER_IP=${var.locust_master_private_ip}" >> /etc/default/locust
systemctl start locust-slave
EOF
  }

  depends_on = ["aws_iam_policy_attachment.fleet"]
}
