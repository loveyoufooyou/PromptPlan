from odoo import models, fields, _
from odoo.exceptions import ValidationError


class PromptTemplateTestSaveTemplateWizard(models.TransientModel):
    _name = 'prompt.template.test.save.wizard'
    _description = 'Prompt Template Test Save Template Wizard'

    name = fields.Char(string='Template Name')
    description = fields.Char(string='Description')
    comment = fields.Char(string='Comment')
    task_id = fields.Many2one(
        comodel_name='prompt.task', string='Task',
    )
    prompt = fields.Text(string='Prompt')
    save_response = fields.Boolean(
        string='Save Response', default=False,
    )

    def save_template(self):
        self.ensure_one()
        if not all((self.name, self.prompt)):
            raise ValidationError(_('Name and Prompt are required'))
        test_id = self._context.get('test_id')
        if not test_id:
            raise ValidationError(_('No test_id provided'))
        test_id = self.env['prompt.template.test'].browse(test_id)
        vals = {
            'name': self.name,
            'description': self.description,
            'comment': self.comment,
            'task_id': self.task_id.id,
            'prompt': self.prompt,
        }
        if self.save_response:
            call_ids_vals = []
            for i in range(1, test_id.test_number+1):
                call_ids_val = test_id.generate_call_ids_val(i)
                if call_ids_val:
                    call_ids_vals.append([0, 0, call_ids_val])
            vals['call_ids'] = call_ids_vals

        template = self.env['prompt.template'].create(vals)
        test_id.prompt_id = template
