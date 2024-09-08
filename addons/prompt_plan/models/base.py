from odoo import models, fields


class BaseLookUpValue(models.Model):
    _name = 'base.lookup.value'
    _description = 'Base Lookup Value'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    value = fields.Char(string='Value')
    type_id = fields.Many2one(comodel_name='base.lookup.type', string='Type')


class BaseLookUpType(models.Model):
    _name = 'base.lookup.type'
    _description = 'Base Lookup Type'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    description = fields.Char(string='Description')
    value_ids = fields.One2many(
        comodel_name='base.lookup.value',
        inverse_name='type_id',
        string='Values',
    )
