#!/bin/bash

pushd ../terraform > /dev/null

LOCUST_MASTER_IP=$(terraform output -json | jq ".girder_ec2_address.value" | sed -e "s/\"//g")

popd > /dev/null

ssh -o StrictHostKeyChecking=no  -i $TF_VAR_key_path -l ubuntu $LOCUST_MASTER_IP $*
