from dotenv import load_dotenv
load_dotenv()
import argparse
import subprocess
import yaml
import os
import re

import shutil

def check_docker():
    if not shutil.which('docker'):
        print("Error: Docker is not installed or not in the system path.")
        exit(1)

def check_dockerfile():
    if not os.path.isfile('Dockerfile'):
        print("Error: Dockerfile does not exist in the current directory.")
        exit(1)

def init():
    config = {
        'service': 'myapp',
        'image': 'image-name',
        'registry': {
            'server': 'registry.server.com',
            'username': 'registry-user-name',
            'password': ['ROCKETSHIP_REGISTRY_PASSWORD']
        }
    }

    os.makedirs('config', exist_ok=True)
    with open('config/deploy.yml', 'w') as f:
        yaml.dump(config, f)

def load_config():
    with open('config/deploy.yml') as f:
        config = yaml.safe_load(f)

    # Replace placeholders with environment variable values
    config = replace_placeholders_in_dict(config)
    return config

def replace_placeholders(value):
    # This regular expression matches placeholders like ${VAR_NAME}
    pattern = re.compile(r'\$\{(.+?)\}')
    return pattern.sub(lambda m: os.getenv(m.group(1)), value)

def replace_placeholders_in_dict(d):
    for key, value in d.items():
        if isinstance(value, str):
            d[key] = replace_placeholders(value)
        elif isinstance(value, dict):
            d[key] = replace_placeholders_in_dict(value)
    return d

def validate_config(config):
    assert 'service' in config and config['service'], "Missing or empty 'service' in config"
    assert 'image' in config and config['image'], "Missing or empty 'image' in config"
    assert 'registry' in config and config['registry'], "Missing or empty 'registry' in config"
    assert 'server' in config['registry'] and config['registry']['server'], "Missing or empty 'server' in registry config"
    assert 'username' in config['registry'] and config['registry']['username'], "Missing or empty 'username' in registry config"
    assert 'password' in config['registry'] and config['registry']['password'], "Missing or empty 'password' in registry config"

def setup():
    check_docker()
    check_dockerfile()
    config = load_config()
    validate_config(config)

    registry = config['registry']
    image = config['image']
    service = config['service']

    # Log into the registry
    try:
        subprocess.run(['docker', 'login', registry['server'], '-u', registry['username'], '--password-stdin'],
                       input=registry['password'], encoding='utf-8', check=True)
    except subprocess.CalledProcessError:
        print("Error logging into Docker registry.")
        return

    # Build the image
    try:
        subprocess.run(['docker', 'build', '-t', image, '.'], check=True)
    except subprocess.CalledProcessError:
        print("Error building Docker image.")
        return

    # Push the image to the registry
    try:
        subprocess.run(['docker', 'push', f'{registry["server"]}/{image}'], check=True)
    except subprocess.CalledProcessError:
        print("Error pushing Docker image to registry.")
        return

    # Pull the image from the registry onto the servers
    # This is a placeholder. You'll need to replace this with the actual command to pull the image on your servers.
    print(f'Pulling image {image} from {registry["server"]} onto servers...')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['init', 'setup'])
    args = parser.parse_args()

    if args.command == 'init':
        init()
    elif args.command == 'setup':
        setup()

if __name__ == "__main__":
    main()