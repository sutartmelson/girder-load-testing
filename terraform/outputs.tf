output "girder_ec2_address" {
  value = "${aws_instance.girder.*.public_ip[0]}"
}

output "locust_master_ec2_address" {
  value = "${aws_instance.locust_master.*.public_ip[0]}"
}

output "locust_slave_spot_fleet_request" {
  value = "${aws_spot_fleet_request.locust_slaves.id}"
}

output "region" {
  value = "${substr(var.zone, 0, length(var.zone) - 1)}"
}
