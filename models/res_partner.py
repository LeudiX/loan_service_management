import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'

    id_number = fields.Char(string='Id Number')
    loan_applicant = fields.Boolean(string='Loan Applicant')

    @api.constrains('id_number')
    def validate_idn(self):
        for record in self:
            if record.id_number:
                if len(record.id_number) != 11 or re.match(r"^[a-zA-z][ a-zA-Z]*", record.id_number):
                    raise ValidationError("Wrong Id number format")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get('loan_applicant'):
                vals['loan_applicant'] = True
        return super(Partner, self).create(vals_list)
