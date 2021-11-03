import argparse
from .main import Main
parser = argparse.ArgumentParser(description='Enter the name of a custom config file')
parser.add_argument('--config', type=str, default="config.json", help="custom config file location")
parser.add_argument('--keys', type=str, default="keys.json", help="custom key file location")

parsed = parser.parse_args()

Main(config_file=parsed.config, keys_file=parsed.keys)
