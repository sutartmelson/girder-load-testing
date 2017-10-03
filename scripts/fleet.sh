#!/bin/bash

pushd ../terraform > /dev/null

# Requires awscli, jq
export AWS_DEFAULT_REGION=$(terraform output -json | jq ".region.value" | sed -e "s/\"//g")
export AWS_ACCESS_KEY_ID=$TF_VAR_access_key
export AWS_SECRET_ACCESS_KEY=$TF_VAR_secret_key

SPOT_REQUEST_ID=$(terraform output -json |\
                      jq ".locust_slave_spot_fleet_request.value" |\
                      sed -e "s/\"//g")


SPOT_INSTANCE_IDS=$(aws ec2 describe-spot-fleet-instances \
                        --spot-fleet-request-id=$SPOT_REQUEST_ID |\
                        jq '.ActiveInstances[].InstanceId' | xargs)

SPOT_INSTANCE_IPS=$(aws ec2 describe-instances \
    --instance-ids $SPOT_INSTANCE_IDS |\
    jq ".Reservations[].Instances[].PublicIpAddress" |\
    sed -e "s/\"//g")

popd > /dev/null


pssh  -i -H "$SPOT_INSTANCE_IPS" -x "-oStrictHostKeyChecking=no  -i $TF_VAR_key_path -l ubuntu" $*
