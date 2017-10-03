variable "zone" {
  type="string"
}

variable "girder_instance_type" {
  type="string"
  default = "m4.4xlarge"
}

variable "locust_instance_type" {
  type="string"
  default = "m4.4xlarge"
}


provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region     = "${substr(var.zone, 0, length(var.zone) - 1)}"
}

data "aws_caller_identity" "current" {}

variable "girder_private_ip" {
  type = "string"
  default = "10.0.1.10"
}

variable "girder_host_url" {
  type = "string"
  default = "http://10.0.1.10:8080"
}


data "aws_ami" "girder_ami" {
  most_recent      = true
  owners = ["${data.aws_caller_identity.current.account_id}"]
  filter {
    name   = "name"
    values = ["girder_load_test_ami*"]
  }
}


resource "aws_instance" "girder" {
  # TODO find better way of viewing AMI https://cloud-images.ubuntu.com/locator/ec2/releasesTable
  ami = "${data.aws_ami.girder_ami.image_id}"
  instance_type = "${var.girder_instance_type}"
  availability_zone      = "${var.zone}"
  key_name = "${var.key_name}"
  iam_instance_profile = "${aws_iam_instance_profile.load_test_user.id}"
  vpc_security_group_ids = ["${aws_security_group.basic.id}"]
  subnet_id = "${aws_subnet.default.id}"
  private_ip = "${var.girder_private_ip}"

  tags {
    Name = "${var.girder_instance_name}"
  }
}

## LOCUST Resources

variable "locust_master_private_ip" {
  type = "string"
  default = "10.0.1.11"
}

data "aws_ami" "locust_ami" {
  most_recent      = true
  owners = ["${data.aws_caller_identity.current.account_id}"]
  filter {
    name   = "name"
    values = ["locust_load_test_ami*"]
  }
}


resource "aws_instance" "locust_master" {
  # TODO find better way of viewing AMI https://cloud-images.ubuntu.com/locator/ec2/releasesTable
  ami = "${data.aws_ami.locust_ami.image_id}"
  instance_type = "${var.locust_instance_type}"
  availability_zone      = "${var.zone}"
  key_name = "${var.key_name}"
  availability_zone      = "${var.zone}"
  iam_instance_profile = "${aws_iam_instance_profile.load_test_user.id}"

  vpc_security_group_ids = ["${aws_security_group.basic.id}"]
  subnet_id = "${aws_subnet.default.id}"

  private_ip = "${var.locust_master_private_ip}"

  user_data = <<EOF
#!/bin/bash
echo "GIRDER_HOST_URL=http://${var.girder_private_ip}:8080" > /etc/default/locust
echo "LOCUST_MASTER_IP=${var.locust_master_private_ip}" >> /etc/default/locust
systemctl start grafana-server locust-master
EOF

  tags {
    Name = "${var.locust_instance_name}"
  }
}
