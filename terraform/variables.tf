variable "access_key" {}
variable "secret_key" {}
variable "key_name" {}
variable "girder_instance_name" {
  default = "girder_load_test_instance"
}
variable "locust_instance_name" {
  default = "locust_master_instance"
}

#variable "s3_force_destroy" {
#  default = false
#  description = "Whether or not to forcibly destroy S3 buckets (whether they have data in them or not)."
#}
