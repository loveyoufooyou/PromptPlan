import logging
import re
import time

from queue import Queue
from threading import Thread
from collections import defaultdict

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from .constants import GRADE_MAPPING, SCORE_MAPPING

_logger = logging.getLogger(__name__)


class PromptTask(models.Model):
    _name = 'prompt.task'
    _description = 'Prompt Task'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    template_ids = fields.One2many(
        comodel_name='prompt.template',
        inverse_name='task_id',
        string='Templates',
    )
    active = fields.Boolean(string='Active', default=True)

    def to_test(self):
        view_id = self.env.ref('prompt_plan.prompt_template_test_view_form').id
        res_id = self.env['prompt.template.test'].create({'task_id': self.id}).id
        return {
            'name': _('Test'),
            'res_model': 'prompt.template.test',
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'view_id': view_id,
            'res_id': res_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def to_prompt_template_view(self):
        view_id = self.env.ref('prompt_plan.prompt_template_view_tree').id
        return {
            'name': _('Prompt Template'),
            'res_model': 'prompt.template',
            'type': 'ir.actions.act_window',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [('task_id', 'in', self.ids)],
            'view_id': view_id,
            'target': 'current',
        }


class PromptTemplate(models.Model):
    _name = 'prompt.template'
    _description = 'Product Template'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    status = fields.Selection([
        ('created', 'Created'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ], string='Status', default='created')
    comment = fields.Char(string='Comment')
    task_id = fields.Many2one(comodel_name='prompt.task', string='Prompt Task')
    active = fields.Boolean(string='Active', default=True)
    prompt = fields.Text(string='Prompt')
    call_ids = fields.One2many(
        comodel_name='prompt.template.call',
        inverse_name='prompt_id',
        string='Calls',
    )
    score = fields.Selection(
        selection=[
            ('A+', 'A+'),
            ('A', 'A'),
            ('B+', 'B+'),
            ('B', 'B'),
            ('C+', 'C+'),
            ('C', 'C'),
        ],
        string='Score',
        compute='_compute_score',
    )

    @api.depends('call_ids.score')
    def _compute_score(self):
        for record in self:
            scores = record.call_ids.filtered(lambda r: r.score).mapped('score')
            if scores:
                numerical_scores = [GRADE_MAPPING[score] for score in scores]
                average_score = round(sum(numerical_scores) / len(numerical_scores))
                record.score = SCORE_MAPPING[average_score]
            else:
                record.score = False

    def confirm_prompt(self):
        for record in self:
            if record.status in ('confirmed', 'rejected'):
                raise ValidationError(_('Prompt is already {}'.format(record.status)))
            else:
                record.status = 'confirmed'

    def reject_prompt(self):
        for record in self:
            if record.status in ('confirmed', 'rejected'):
                raise ValidationError(_('Prompt is already {}'.format(record.status)))
            else:
                record.status = 'rejected'

    def to_test(self):
        view_id = self.env.ref('prompt_plan.prompt_template_test_view_form').id
        res_id = self.env['prompt.template.test'].create({
            'task_id': self.task_id.id,
            'prompt_id': self.id,
            'prompt': self.prompt,
        }).id
        return {
            'name': _('Test'),
            'res_model': 'prompt.template.test',
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'view_id': view_id,
            'res_id': res_id,
            'view_mode': 'form',
            'target': 'current',
        }


class PromptTemplateCall(models.Model):
    _name = 'prompt.template.call'
    _description = 'Prompt Template Call'

    prompt_id = fields.Many2one(comodel_name='prompt.template', string='Prompt')
    input = fields.Text(string='Input')
    model_id = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'Model')],
        string='Model',
    )
    env_id = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'PythonEnvironment')],
        string='Environment',
    )
    setting_id = fields.Many2one(
        comodel_name='prompt.template.settings',
        string='Setting',
    )
    response = fields.Text(string='Response')
    score = fields.Selection(
        selection=[
            ('A+', 'A+'),
            ('A', 'A'),
            ('B+', 'B+'),
            ('B', 'B'),
            ('C+', 'C+'),
            ('C', 'C'),
        ],
        string='Score',
    )


class PromptTemplateTest(models.TransientModel):
    _name = 'prompt.template.test'
    _description = 'Prompt Template Test'
    _rec_name = 'task_id'

    task_id = fields.Many2one(comodel_name='prompt.task', string='Prompt Task')
    prompt_id = fields.Many2one(comodel_name='prompt.template', string='Prompt')
    test_number = fields.Integer(string='Test Number', default=1)
    prompt = fields.Text(string='Prompt')
    input = fields.Text(string='Input')

    check1 = fields.Boolean(string='Check', default=True)
    project_id1 = fields.Many2one(
        comodel_name='prompt.template.test.project',
        string='Project'
    )
    model_id1 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'Model')],
        string='Model',
    )
    env_id1 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'PythonEnvironment')],
        string='Environment',
    )
    setting_id1 = fields.Many2one(
        comodel_name='prompt.template.test.settings',
        string='Setting',
    )
    score1 = fields.Selection(
        selection=[
            ('A+', 'A+'),
            ('A', 'A'),
            ('B+', 'B+'),
            ('B', 'B'),
            ('C+', 'C+'),
            ('C', 'C'),
        ],
        string='Score',
    )
    response1 = fields.Text(string='Response')

    check2 = fields.Boolean(string='Check', default=True)
    project_id2 = fields.Many2one(
        comodel_name='prompt.template.test.project',
        string='Project'
    )
    model_id2 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'Model')],
        string='Model',
    )
    env_id2 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'PythonEnvironment')],
        string='Environment',
    )
    setting_id2 = fields.Many2one(
        comodel_name='prompt.template.test.settings',
        string='Setting',
    )
    score2 = fields.Selection(
        selection=[
            ('A+', 'A+'),
            ('A', 'A'),
            ('B+', 'B+'),
            ('B', 'B'),
            ('C+', 'C+'),
            ('C', 'C'),
        ],
        string='Score',
    )
    response2 = fields.Text(string='Response')

    check3 = fields.Boolean(string='Check', default=True)
    project_id3 = fields.Many2one(
        comodel_name='prompt.template.test.project',
        string='Project'
    )
    model_id3 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'Model')],
        string='Model',
    )
    env_id3 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'PythonEnvironment')],
        string='Environment',
    )
    setting_id3 = fields.Many2one(
        comodel_name='prompt.template.test.settings',
        string='Setting',
    )
    score3 = fields.Selection(
        selection=[
            ('A+', 'A+'),
            ('A', 'A'),
            ('B+', 'B+'),
            ('B', 'B'),
            ('C+', 'C+'),
            ('C', 'C'),
        ],
        string='Score',
    )
    response3 = fields.Text(string='Response')

    check4 = fields.Boolean(string='Check', default=True)
    project_id4 = fields.Many2one(
        comodel_name='prompt.template.test.project',
        string='Project'
    )
    model_id4 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'Model')],
        string='Model',
    )
    env_id4 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'PythonEnvironment')],
        string='Environment',
    )
    setting_id4 = fields.Many2one(
        comodel_name='prompt.template.test.settings',
        string='Setting',
    )
    score4 = fields.Selection(
        selection=[
            ('A+', 'A+'),
            ('A', 'A'),
            ('B+', 'B+'),
            ('B', 'B'),
            ('C+', 'C+'),
            ('C', 'C'),
        ],
        string='Score',
    )
    response4 = fields.Text(string='Response')

    check5 = fields.Boolean(string='Check', default=True)
    project_id5 = fields.Many2one(
        comodel_name='prompt.template.test.project',
        string='Project'
    )
    model_id5 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'Model')],
        string='Model',
    )
    env_id5 = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'PythonEnvironment')],
        string='Environment',
    )
    setting_id5 = fields.Many2one(
        comodel_name='prompt.template.test.settings',
        string='Setting',
    )
    score5 = fields.Selection(
        selection=[
            ('A+', 'A+'),
            ('A', 'A'),
            ('B+', 'B+'),
            ('B', 'B'),
            ('C+', 'C+'),
            ('C', 'C'),
        ],
        string='Score',
    )
    response5 = fields.Text(string='Response')

    def invoke(self):
        invoke_records = []
        for record in self:
            for i in range(1, record.test_number+1):
                if getattr(record, f'check{i}') is True:
                    project_id = getattr(record, f'project_id{i}')
                    response = ''
                    attachment = None
                    if project_id:
                        if project_id.is_security_file:
                            attachment = project_id.attachment_ids[0]
                        invoke_model_id = project_id.invoke_model_id
                    if invoke_model_id:
                        settings = self.get_settings(i)
                        invoke_records.append({
                            'id': record._origin.id,
                            'index': i,
                            'model': invoke_model_id.value,
                            'input': {
                                'attachment': attachment,
                                'prompt': record.prompt,
                                'input': record.input,
                                'exe_path': getattr(record, f'env_id{i}').value,
                                'settings': settings,
                            }
                        })

        def run_subprocess_thread(rec_id, model, index, input, queue):
            try:
                response = self.env[model].invoke(input)
                queue.put(f'[{rec_id}:{index}]{response}')
            except Exception as e:
                queue.put(f'[{rec_id}:{index}]{e}')
        _logger.info(f'invoke_records: {invoke_records}')
        result_queue = Queue()
        threads = []
        for invoke in invoke_records:
            thread = Thread(
                target=run_subprocess_thread,
                args=(invoke['id'], invoke['model'], invoke['index'],
                      invoke['input'], result_queue),
            )
            thread.start()
            threads.append(thread)
            time.sleep(0.3)
        for t in threads:
            t.join()
        results = defaultdict(dict)
        while not result_queue.empty():
            data = result_queue.get()
            match_res = re.match(r'\[(\w+):(\d+)\]', data)
            if match_res:
                rec_id = int(match_res.group(1))
                index = int(match_res.group(2))
                results[rec_id][index] = data[len(match_res.group(0)):]
        for recode in self:
            update_val = {}
            for i in range(1, record.test_number+1):
                response = results[recode._origin.id].get(i)
                if response:
                    update_val.update({
                        f'response{i}': response,
                        f'score{i}': False,
                    })
            if update_val:
                record.write(update_val)

    def save_template(self):
        self.ensure_one()
        if self.prompt_id:
            raise ValidationError(
                _('Not allowed to change existing prompt template, '
                'please set none to prompt_id field first.')
            )
        model_name = 'prompt.template.test.save.wizard'
        res_id = self.env[model_name].create({
            'task_id': self.task_id.id,
            'prompt': self.prompt,
            'description': self.task_id.description,
        }).id
        view_id = self.env.ref(
            'prompt_plan.prompt_template_test_save_wizard_view_form'
        ).id
        return {
            'name': _('Save Prompt Template'),
            'type': 'ir.actions.act_window',
            'res_model': model_name,
            'views': [[False, 'form']],
            'view_id': view_id,
            'res_id': res_id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'test_id': self.id,
            }
        }
 
    def generate_call_ids_val(self, i):
        self.ensure_one()
        check = getattr(self, f'check{i}')
        model_id = getattr(self, f'model_id{i}')
        response = getattr(self, f'response{i}')
        env_id = getattr(self, f'env_id{i}')
        setting_id = getattr(self, f'setting_id{i}')
        score = getattr(self, f'score{i}')
        if all((check, model_id, score, response)):
            persistence_setting_id = setting_id.persistence()
            val = {
                'prompt_id': self.prompt_id.id,
                'input': self.input,
                'model_id': model_id.id,
                'env_id': env_id.id,
                'setting_id': (
                    persistence_setting_id.id
                    if persistence_setting_id else False
                ),
                'response': response,
                'score': score,
            }
        else:
            val = {}
        return val

    def save_call(self):
        self.ensure_one()
        if not self.prompt_id:
            raise ValidationError(_('Please select a prompt template'))
        response_index = self._context.get('response_index')
        if response_index and (1 <= response_index <= self.test_number):
            call_ids_val = self.generate_call_ids_val(response_index)
            if call_ids_val:
                self.env['prompt.template.call'].create(call_ids_val)
            else:
                raise ValidationError(
                    _('Please fill in all required fields, Model & Check & Score & Response.')
                )
        else:
            raise ValidationError(
                _('Error: 1 <= response_index:{response_index} <= {test_number}'.format(
                    response_index=response_index, test_number=self.test_number,
                ))
            )

    @api.onchange('prompt_id')
    def _onchange_prompt_id(self):
        if self.prompt_id:
            self.prompt = self.prompt_id.prompt

    def get_settings(self, index):
        self.ensure_one()
        model_id = getattr(self, f'model_id{index}')
        setting_id = getattr(self, f'setting_id{index}')
        filter_fields = ['name', 'id', 'create_uid', 'create_date', 'write_uid', 'write_date']
        settings = {
            field: getattr(setting_id, field)
            for field in setting_id._fields if field not in filter_fields
        }
        settings['model'] = model_id.value
        return settings


class PromptTemplateSettings(models.Model):
    _name = 'prompt.template.settings'
    _description = 'Prompt Template Settings'

    name = fields.Char(string='Name')
    temperature = fields.Float(string='Temperature', default=1)
    n = fields.Integer(string='N', default=1)
    max_tokens = fields.Integer(string='Max Tokens', default=256)
    presence_penalty = fields.Float(string='Presence Penalty', default=0)
    frequency_penalty = fields.Float(string='Frequency Penalty', default=0)
    stream = fields.Boolean(string='Stream', default=False)


class PromptTemplateTestSettings(models.TransientModel):
    _inherit = 'prompt.template.settings'
    _name = 'prompt.template.test.settings'
    _description = 'Prompt Template Test Settings'

    def get_formview_action(self, access_uid=None):
        res = super().get_formview_action(access_uid)
        res.update({
            'name': _('Settings'),
            'target': 'new',
        })
        return res

    def persistence(self):
        if not self:
            return False
        self.ensure_one()
        vals = {
            'name': self.name,
            'temperature': self.temperature,
            'n': self.n,
            'max_tokens': self.max_tokens,
            'presence_penalty': self.presence_penalty,
            'frequency_penalty': self.frequency_penalty,
            'stream': self.stream,
        }
        return self.env['prompt.template.settings'].create(vals)


class PromptTemplateTestProject(models.Model):
    _name = 'prompt.template.test.project'
    _description = 'Prompt Template Test Project'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description')
    is_security_file = fields.Boolean(
        string='Security File', default=False,
        help='When it is set to True, the execution uses attachments.',
    )
    attachment_ids = fields.Many2many(
        comodel_name='ir.attachment', string='Attachment',
        relation='test_project_attachment_rel',
        column1='test_project_id', column2='attachment_id',
        help='Only the first file will be used.',
    )
    attachment_count = fields.Integer(
        string='Attachment Count', compute='_compute_attachment_len',
    )
    status = fields.Selection(
        selection=[('created', 'Created'), ('confirmed', 'Confirmed')],
        string='Status', default='created',
    )
    invoke_model_id = fields.Many2one(
        comodel_name='base.lookup.value',
        domain=[('type_id.code', '=', 'InvokeModel')],
        string='Invoke Model',
    )

    @api.depends('attachment_ids')
    def _compute_attachment_len(self):
        for record in self:
            record.attachment_count = len(self.attachment_ids)
