# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
"""_Stores partial payments, linking each to a loan_
"""


class Loan_payment(models.Model):
    _name = "loan.payment"
    _description = "Loan Payment"

    loan_id = fields.Many2one(
        string=_("Loan"), comodel_name="loan.service", required=True
    )
    # Feature (Retrieve the partner_id.name from the related loan.service [Improves performance] )
    partner_id = fields.Many2one(
        string="Customer",
        related="loan_id.partner_id",
        store=True,
        readonly=True,
    )
    payment_date = fields.Date(
        string=_("Payment Date"),
        default=fields.Date.context_today,  # Question context_today vs date?
    )
    amount = fields.Float(string=_("Amount Paid"), required=True)
    payment_method = fields.Selection(
        string=_("Payment Method"),
        selection=[
            ("cash", "Cash"),
            ("bank_transfer", "Bank Transfer"),
            ("mobile_payment", "Mobile Payment"),
        ],
        required=True,
    )

    @api.model_create_multi
    def create(self, vals):
        record = super().create(vals)
        record.loan_id._compute_remaining_debt()
        return record

    @api.constrains("loan_id", "payment_date")
    def _check_monthly_payment(self):
        for record in self:
            last_payment = self.search(
                [("loan_id", "=", record.loan_id.id)],
                order="payment_date desc",
                limit=1,
            )
            if (
                last_payment
                and (record.payment_date - last_payment.payment_date).days < 30
            ):
                raise ValidationError("Payments can only be  mande once per month")
