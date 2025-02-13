import re

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Partner(models.Model):
    _inherit = "res.partner"

    id_number = fields.Char(string="Id Number")
    loan_applicant = fields.Boolean(string="Loan Applicant")

    def is_valid_id_number(self, id_number):
        """_Check if the ID number is valid_

        Args:
            id_number (_Integer_): _The applicant id number_

        Returns:
            bool: True if the ID number is valid, False otherwise
        """
        is_valid_length = len(id_number) == 11
        contains_invalid_chars = re.match(r"^[a-zA-Z][ a-zA-Z]*$", id_number)

        return is_valid_length and not contains_invalid_chars

    @api.constrains("id_number")
    def validate_idn(self):
        for record in self:
            if record.id_number:
                if not self.is_valid_id_number(record.id_number):
                    raise ValidationError("Wrong Id number format")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if self.env.context.get("loan_applicant"):
                vals["loan_applicant"] = True
        return super(Partner, self).create(vals_list)
