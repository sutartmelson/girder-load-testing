# Girder Load Testing Infrastructure

The following repository contains scripts and IaC artifacts for launching AWS infrastructure that is suitable for running load testing on Girder. Load testing is performed with [Locust IO](https://docs.locust.io/en/latest/) and reports metrics to [Graphite](http://graphite.readthedocs.io/en/latest/) which can be visualized in real time using [Grafana](http://docs.grafana.org/). 

The current code creates two on-demand instances and a variable number of AWS spot instances. The two on-demand instances are the "Girder Instance" and the "Locust Master" instance. The Girder instance is provisioned with nginx, Girder and mongodb. Exact details for the configuration of the Girder instance can be found in ```packer/girder/site.yml```. The second instance "Locust Master" is provisioned with a systemd service for running the locust master daemon, Graphite and Grafana. AWS spot instances are launched with the same AMI as the locust master instance and have a systemd service for running the locust slave daemon. Exact details of the Locust Master and Slave instance configurations can be found in ```packer/locustio/site.yml```.

![girder load testing architecture](https://docs.google.com/drawings/d/e/2PACX-1vQoFNtJBjT1wTT5J2ZyL933i4M33LM2WoWzb2QqswfzcprBn-JBcw9pDt8p9oj48CqqYBR2WTjm1JKb/pub?w=960&h=720)

## Technologies

To bring up this infrastructure we use [Packer](https://www.packer.io/docs/index.html),  [Ansible](http://docs.ansible.com/ansible/latest/index.html),  and [Terraform](https://www.terraform.io/docs/index.html).  Packer is used to generate AWS AMI's for Girder and the Locust Master/Slave instances. Packer does this by creating temporary instances from a default Ubuntu 16.04 AWS image, provisioning those instances with Ansible, generating the AMI's and then destroying the instance. Once AMIs are generated,  the full infrastructure is launched and managed with Terraform. 

# Getting Started

## Requirements

### Terraform
https://www.terraform.io/downloads.html

### Packer
https://www.packer.io/downloads.html

### jq
jq must be available and on your PATH: https://stedolan.github.io/jq/.

### AWS CLI
http://docs.aws.amazon.com/cli/latest/userguide/installing.html

### Script dependencies
Several of the scripts in the ```scripts/``` folder require certain python dependencies. These can be installed with:
```
pip install -r scripts/requirements.txt
```

## Secrets
Begin by copying ```secrets.example``` to ```secrets``` in the root directory of this repository.

+ ```TF_VAR_access_key``` should coorispond to you AWS\_ACCESS\_KEY\_ID
+ ```TF_VAR_secret_key``` should coorispond to your  AWS\_SECRET\_ACCESS\_KEY. 
+ ```TF_VAR_key_name``` should be the string name of [IAM Access Key](http://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html) and 
+ ```TF_VAR_key_path``` should be the full path to the .pem file that corresponds with your IAM Access Key. 

You must source the ```secrets``` file in any terminal you wish to work in. Do this by running:
```
source secrets
```
from the command line in the root directory of this repository.

## Build Images

### Build the Girder Image
```
cd packer/girder/
packer build packer.json
```

### Build the Locust Image
```
cd packer/locustio/
packer build packer.json
```

## Launch the Infrastructure

```
cd terraform/
terraform init
terraform apply
```

This will prompt for certain variables needed to launch the spot instances. 
+```spot_bid``` which is the amount you wish to bid for the spot instances
+ ```spot_num``` The number of spot instances to launch _(Note: this number must be less than your_ [AWS Service Limit](http://docs.aws.amazon.com/general/latest/gr/aws_service_limits.html) _for you instance type)_
+ ```zone``` The availability zone (e.g. "us-east-1b") in which you wish to launch the infrastructure. _(Note: spot price varies across availability zones)_

### Spot bid price
To determine an appropriate you spot bid price,  use the ```scripts/aws_pricing.py``` script (Documentation for this script is available in the ```script/``` directory). 

### Instance types
By default this will launch Girder and the Locust Master on an m4.4xlarge instances.  Locust Slaves will be launched on m4.large instances. To change this you may use the ```girder_instance_type```, ```locust_instance_type``` and ```spot_instance_type``` variables. E.g.:

```
terraform apply \
-var 'girder_instance_type=m4.10xlarge' \
-var 'locust_instance_type=m4.10xlarge' \
-var 'spot_instance_type=t2.micro'
```

### Reading variables from a file

Multiple calls to terraform apply/destroy will re-prompt for variables. This can be frustrating when creating and destroying infrastructure often. To ameliorate this place variables in ```terraform.tfvars``` file along side ```main.tf```.  This file might look like the following:

```
spot_bid = "0.025"
spot_num = "10"
zone     = "us-east-1b"

# Command line variables may also be included
# girder_instance_type = "m4.10xlarge"
# locust_instance_type = "m4.10xlarge"
# spot_instance_type   = "t2.micro" 
```

## Accessing Services

After successfully running ```terraform apply``` terraform will print out IP addresses of the girder and locust master instances. 
+ Girder is accessible at http://${girder\_ec2\_address}:8080
  + The username and password are ```girder``` and ```girder```
+ Locust Master is accessible at http://${locust\_master\_ec2\_address}:8089
+ Grafana is accessible at http://${locust\_master\_ec2\_address}:3000
  + The username and password are ```admin``` and ```admin```


# Repository directory structure

+ ```packer/``` files and folders related to creating AWS AMIs using packer
+ ```terraform/``` terraform files for launching infrastructure
+ ```scripts/``` various scripts and utilities that support launching infrastructure and developing locust files. 
  + See ```scripts/README.md``` for more information about script usage and development workflow. 
