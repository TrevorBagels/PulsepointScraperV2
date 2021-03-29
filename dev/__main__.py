import argparse
from .main import Main
parser = argparse.ArgumentParser(description='Enter the name of a custom config file')
parser.add_argument('--config', type=str, nargs='+', help="custom config file location")
cfg = "config.json"
parsed = parser.parse_args()
if parsed.config != None:
	cfg = parsed.config[0]
Main(config_file=cfg)
