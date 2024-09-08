import base64
import glob
import io
import json
import logging
import os
import shutil
import tarfile
import tempfile
import time
import zipfile
from typing import Dict

from .base import BasePromptModelInvoke
from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SubprocessInvoke(BasePromptModelInvoke):
    _name = 'subprocess.invoke'
    _description = 'Subprocess Invoke'

    def get_unzipped_name(self, filename):
        extensions = ['.zip', '.tar', '.tar.gz']
        for ext in extensions:
            if filename.endswith(ext):
                return filename[:-len(ext)], ext
        return filename, os.path.splitext(filename)[1]

    def get_files_matching_pattern(self, directory_path, pattern):
        full_pattern = os.path.join(directory_path, pattern)
        matching_files = glob.glob(full_pattern)
        return matching_files[0]

    def extract_file(self, file_data, output_dir, ext):
        if ext == '.zip':
            with zipfile.ZipFile(file_data, 'r') as zip_file:
                zip_file.extractall(output_dir)
            return True
        elif ext == '.tar.gz':
            with tarfile.open(fileobj=file_data, mode='r:gz') as tar:
                tar.extractall(path=output_dir)
            return True
        elif ext == '.tar':
            with tarfile.open(fileobj=file_data, mode='r') as tar:
                tar.extractall(path=output_dir)
            return True
        return False

    def check_input(self, input: Dict):
        required_attrs = {'attachment', 'prompt', 'input', 'exe_path'}
        input_attrs = {
            k for k, v in input.items()
            if v is not None and v != '' and v is not False
        }
        if not required_attrs.issubset(input_attrs):
            raise ValidationError(
                _('Missing required attributes: {}').format(
                    ', '.join(required_attrs - input_attrs)
                )
            )

    def invoke(self, input: Dict):
        self.check_input(input)
        attachment = input['attachment']
        file_content = attachment.with_context(bin_size=False).datas
        dirname, ext = self.get_unzipped_name(attachment.name)
        file_data = io.BytesIO(base64.b64decode(file_content))
        temp_dir = tempfile.mkdtemp()
        extract_state = self.extract_file(file_data, temp_dir, ext)
        if extract_state is False:
            raise Exception(
                _('Unsupported file format \"{}\", '
                  'import only supports .zip, .tar and .tar.gz').format(ext)
            )

        main_path = self.get_files_matching_pattern(
            directory_path=os.path.join(temp_dir, dirname),
            pattern='main.*',
        )
        cur_time = time.time()
        response = self.invoke_subprocess(
            exe_path=input['exe_path'],
            script_path=main_path,
            extra_args=[
                '-p', input['prompt'],
                '-i', input['input'],
                '-s', json.dumps(input['settings']),
            ],
        )
        _logger.info(f'use time: {time.time() - cur_time}s')
        shutil.rmtree(temp_dir)
        if response['returncode'] == 0:
            return response['output']
        else:
            raise Exception(response['output'])
