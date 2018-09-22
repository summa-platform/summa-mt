#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import yaml
import requests
import logging

MODEL_BASE_URL = os.environ.get('MODEL_BASE_URL', 'http://data.statmt.org/summa/mt/models/')
MODEL_URL = os.environ.get('MODEL_URL', os.path.join(MODEL_BASE_URL, '{source}-{target}/{model}/{filename}'))
MODEL_INFO_FILE = "model_info.yaml"

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s: %(levelname)s:  %(message)s')

logger = logging.getLogger(__name__)


def get_last_model_info(src, trg):
    """
    Download model_info file fom server.

    Args:
        src (str): source language (ISO 639-1 format)
        trg (str): target language (ISO 639-1 format)

    Returns:
        string: content of model_info.yaml file.
    """
    requested_model = os.environ['MARIAN_MODEL']
    model_info_url = MODEL_URL.format(source=src, target=trg, model=requested_model, filename=MODEL_INFO_FILE)
    request = requests.get(model_info_url)
    if request.status_code != 200:
        logger.error("Cannot download model_info file from server.")
    return request.text


def download_file_and_save(path, url):
    """
    Download a file.

    Args:
        path (str): a destination
        url (str): address from a file is downloaded

    Returns:
        bool: False if cannot download a file. Otherwise, true.
    """
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        with open(path, 'wb') as f:
            logger.info('Downloading to %s', path)
            downloaded = 0
            K = 1024
            M = K*K
            checkpoint_step = 10*M # 10MB
            next_checkpoint = checkpoint_step
            for chunk in request:
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded >= next_checkpoint:
                    logger.info('%.1f MB completed' % (downloaded / M))
                    next_checkpoint = downloaded + checkpoint_step
            logger.info('Download complete (%.1f %sB)' % (downloaded / (M if downloaded >= M else K), 'M' if downloaded >= M else 'K'))
    else:
        return False
    return True


def remove_old_model(workdir):
    """
    Remove old model files.

    Args:
        workdir (str): working directory to clean
    """
    logger.debug("Cleaning working directory: {}".format(workdir))
    for filename in os.listdir(workdir):
        os.remove(os.path.join(workdir, filename))


def check_model_update(src, trg, workdir):
    """
    Check whether a new model was uploded to the server.

    Args:
        src (str): source language (ISO 639-1 format)
        trg (str): target language (ISO 639-1 format)
        workdir (str): path to work directory

    Returns:
        bool: True if a new model was uploaded. Otherwise, false.
    """

    if not os.path.isfile(os.path.join(workdir, MODEL_INFO_FILE)):
        logger.debug("Cannot find local model_info file. Force download")
        return True

    with open(os.path.join(workdir, MODEL_INFO_FILE), 'r') as f:
        current_model_info = yaml.load(f.read())

    docker_model = int(os.environ['MARIAN_MODEL'])
    current_model = int(''.join(str(current_model_info['date']).split('-')))
    if docker_model != current_model:
        return True
    else:
        return False


def download_new_model(src, trg, workdir):
    """
    Download new model files.

    Args:
        src (str): source language (ISO 639-1 format)
        trg (str): target language (ISO 639-1 format)
        workdir (str): path to work directory
    """
    model_info = yaml.load(get_last_model_info(src, trg))
    files_to_download = model_info['files'] + [MODEL_INFO_FILE]
    for filename in files_to_download:
        path = os.path.join(workdir, filename)
        model_version = os.environ['MARIAN_MODEL']
        full_url = MODEL_URL.format(source=src, target=trg, model=model_version, filename=filename)

        logger.debug("Downloading: {} to {}".format(full_url, path))
        download_file_and_save(path, full_url)


def update_model(src, trg, workdir, force=False):
    """
    Update SUMMA MT model.

    Args:
        src (str): source language (ISO 639-1 format)
        trg (str): target language (ISO 639-1 format)
        workdir (str): path to work directory
        force (bool): force update

    Returns:
        bool: True if model was successfuly updated. Otherwise, false.
    """
    if check_model_update(src, trg, workdir):
        logger.debug("Founded new model on the server.")

        remove_old_model(workdir)
        download_new_model(src, trg, workdir)
    else:
        logger.debug("The lastest model is already downloaded.")
        return False
    return True


def parse_args():
    """
    parse command arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", dest="workdir", default='.')
    parser.add_argument('-m', dest="model", default='en-de')
    parser.add_argument('-f', dest="force", default=False)
    return parser.parse_args()


def main():
    """ main """
    args = parse_args()
    src = args.model.split('-')[0]
    trg = args.model.split('-')[1]
    workdir = os.path.abspath(args.workdir)
    force = args.force

    try:
        os.makedirs(workdir)
    except OSError:
        pass

    update_model(src, trg, workdir, force)


if __name__ == "__main__":
    main()
