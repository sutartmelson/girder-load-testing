# Portions of this terraform file taken from the two-tier example
# https://github.com/terraform-providers/terraform-provider-aws/blob/master/examples/two-tier/main.tf

# Create a VPC to launch our instances into
resource "aws_vpc" "default" {
  cidr_block = "10.0.0.0/16"

  enable_dns_hostnames = true
}

# Create an internet gateway to give our subnet access to the outside world
resource "aws_internet_gateway" "default" {
  vpc_id = "${aws_vpc.default.id}"
}

# Grant the VPC internet access on its main route table
resource "aws_route" "internet_access" {
  route_table_id         = "${aws_vpc.default.main_route_table_id}"
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = "${aws_internet_gateway.default.id}"
}

# Create a subnet to launch our instances into
resource "aws_subnet" "default" {
  vpc_id                  = "${aws_vpc.default.id}"
  cidr_block              = "10.0.1.0/24"
  availability_zone      = "${var.zone}"
  map_public_ip_on_launch = true
}

resource "aws_security_group" "basic" {
  description = "Allow all inbound traffic for HTTP, SSH for KHQ/KRS."

  vpc_id = "${aws_vpc.default.id}"

  ingress {
    from_port = 0
    to_port = 0
    protocol = -1
    cidr_blocks = [
      "66.194.253.20/32", # KHQ
      "97.65.130.169/32" # KRS
    ]
  }

  ingress {
    from_port = 0
    to_port = 0
    protocol = -1
    self = true
  }


  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
