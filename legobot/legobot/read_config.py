import configparser
import os
import shutil

def _config_filename() -> str:
    return "robot_config.ini"

def get_local_config():
    """Path to the users config file"""
    return os.path.join("./", _config_filename())

def get_repo_config():
    """Path to the config in the git repo"""
    return os.path.join(os.path.dirname(
            os.path.abspath(__file__)), _config_filename())

def get_config_path():
    """Fetch and return the path of the configuration file for connecting to the robot."""
    # First try locally
    path = get_local_config()
    if not os.path.isfile(path):
        # Fallback, use the central config file in the repo
        path = get_repo_config()
    
    return path


def get_config():
    """Parse the configuration details (IP and password) from the configuration file and return."""
    config = configparser.ConfigParser()
    config.read(get_config_path())
    return config

def copy_config(override=False) -> None:
    local = get_local_config()
    repo = get_repo_config()
    
    if not override and os.path.isfile(local):
        print("Local config file {} already exists".format(local))
        return
    
    if not os.path.isfile(repo):
        raise RuntimeError("Repo config file {} doesn't exist".format(repo))
    
    local_dir = os.path.dirname(local)
    # Create the directory
    os.makedirs(local_dir, exist_ok=True)
    
    # Copy from repo to local
    shutil.copyfile(repo, local)


def has_profile(profilename):
    config = get_config()
    return profilename in config


def get_profile(profilename):
    config = get_config()
    return config[profilename]
