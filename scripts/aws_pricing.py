import requests
import click
import boto3
import datetime
import pandas as pd
import os

class SpotPriceQuery(object):
    # Pricing only available for Virginia (us-east-1)?
    # See: http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html
    BASE_URL = "https://pricing.us-east-1.amazonaws.com"
    SERVICE_CODE_URL = "{base_url}/offers/v1.0/aws/index.json"

    def __init__(self, region, instance_types):
        self.region = region

        self.instance_types = [instance_types] \
            if isinstance(instance_types, str) else instance_types

        self.ec2_client = boto3.client(
            'ec2', region_name=region,
            aws_access_key_id=os.environ.get("TF_VAR_access_key", None),
            aws_secret_access_key=os.environ.get("TF_VAR_secret_key", None))
        # URL to pull the
        self.base_url = self.BASE_URL.format(**{**locals(), **self.__dict__})

        self._region_data = None

    # See: https://aws.amazon.com/blogs/aws/new-aws-price-list-api/
    def _service_code_urls(self):
        r = requests.get(self.SERVICE_CODE_URL.format(**{**locals(), **self.__dict__}))
        r.raise_for_status()

        return r.json()['offers']

    def _ec2_region_code_url(self):
        r = requests.get(self.base_url + self._service_code_urls()['AmazonEC2']['currentRegionIndexUrl'])
        r.raise_for_status()
        _ec2_region_codes = r.json()
        _region_uri = _ec2_region_codes['regions'][self.region]['currentVersionUrl']

        return self.base_url + _region_uri

    @property
    def region_data(self):
        if self._region_data is None:
            r = requests.get(self._ec2_region_code_url())
            r.raise_for_status()

            self._region_data = r.json()
        return self._region_data


    def ondemand_compute_products(self, **kwargs):

        def _is_valid_product(i):
            for key, value in kwargs.items():
                target = [value] if isinstance(value, str) else value
                if key not in i:
                    if key not in i['attributes']:
                        return False
                    elif i['attributes'][key] not in target:
                        return False
                elif i[key] not in target:
                    return False
            return True


        def _pricing_data(sku):
            _, pricing = list(self.region_data['terms']['OnDemand'][sku].items())[0]

            assert len(list(pricing['priceDimensions'].items())) == 1

            pricingDimensions = list(pricing['priceDimensions'].items())[0][1]

            return {'pricePerUnit': float(pricingDimensions['pricePerUnit']['USD']),
                    'unit': pricingDimensions['unit']}


        # Only pull Comput Instances with Operating system's of 'Linux'
        # and 'Shared' tenancy (the default for on demand instances)
        for sku, attributes in self.region_data['products'].items():
            if _is_valid_product(attributes):
                yield {**attributes['attributes'], **{'sku': sku}, **_pricing_data(sku)}

    def spot_prices(self, hours=48):
        df = None

        price_paginator = self.ec2_client.get_paginator('describe_spot_price_history')
        price_iterator = price_paginator.paginate(
            InstanceTypes=self.instance_types,
            ProductDescriptions=['Linux/UNIX'],
            StartTime= datetime.datetime.now() - datetime.timedelta(hours=hours),
            EndTime= datetime.datetime.now()
        )

        for page in price_iterator:
            df = pd.DataFrame(page['SpotPriceHistory']) if df is None else \
                 df.append(pd.DataFrame(page['SpotPriceHistory']), ignore_index=True)

        df['Timestamp'] = pd.DatetimeIndex(df['Timestamp'])

        df.set_index('Timestamp', inplace=True)

        del df['InstanceType']
        del df['ProductDescription']

        df['SpotPrice'] = df['SpotPrice'].astype(float)

        df = pd.concat([g.set_index('Timestamp')['SpotPrice'].to_frame(n)
                        for n, g in df.reset_index().groupby('AvailabilityZone')], axis=1)

        return df

    def ondemand_prices(self, columns=('sku', 'instanceType', 'instanceFamily',
                                       'vcpu', 'memory', 'networkPerformance', 'storage',
                                       'pricePerUnit'), **kwargs):

        return pd.DataFrame(self.ondemand_compute_products(**kwargs),
                            columns=columns)\
                 .set_index('sku')\
                 .sort_values(['instanceFamily', 'vcpu'], ascending=False)



@click.command()
@click.argument('region', default='us-east-1')
@click.argument('instance_type', default='m4.large')
@click.option('--ondemand/--no-ondemand', default=False, help='Print ondemand price')
def main(region, instance_type, ondemand):

    spq = SpotPriceQuery(region, instance_type)

    df = spq.spot_prices(hours=6)

    if ondemand:
        od_df = spq.ondemand_prices(productFamily='Compute Instance',
                                    operatingSystem='Linux',
                                    instanceType=instance_type,
                                    tenancy='Shared')

        df['On Demand'] = od_df.iloc[0]['pricePerUnit']

    df = pd.concat([
        # Resample by Hour
        df.fillna(method='pad').resample("H").mean(),
        # Append last known price for each zone
        df.fillna(method='pad').loc[df.index.max()].to_frame().T]).fillna(method='pad')

    print(df.to_string())


if __name__ == "__main__":
    main()
