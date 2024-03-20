import os


def get_repository_path(config_repository):
    return os.path.split(config_repository)[0]


def get_repository_db_name(config_repository):
    return os.path.split(config_repository)[1]
