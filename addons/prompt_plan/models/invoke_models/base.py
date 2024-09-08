import logging
import subprocess
from typing import Dict

from odoo import models

_logger = logging.getLogger(__name__)


class BasePromptModelInvoke(models.AbstractModel):
    _name = 'base.prompt.model.invoke'
    _description = 'Base Prompt Model Invoke'

    def invoke(self, input: Dict):
        """invoke model
        """

    def invoke_subprocess(
        self, exe_path: str, script_path: str, extra_args: list,
    ) -> Dict:
        """invoke model by subprocess
        """
        try:
            args = [exe_path, script_path] + extra_args
            _logger.info(f'invoke subprocess: {args}')
            result = subprocess.run(
                args=args,
                shell=False,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            response = {
                'status': 'success',
                'returncode': result.returncode,
                'output': result.stdout,
            }
        except subprocess.CalledProcessError as e:
            response = {
                'status': 'error',
                'returncode': 1,
                'output': e.stderr,
            }
            _logger.error(response)
        except Exception as e:
            response = {
                'status': 'error',
                'returncode': -1,
                'output': str(e),
            }
            _logger.error(response)
        return response
