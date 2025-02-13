from odoo import models, fields, api
from datetime import date


class LoanService(models.Model):
    _name = "loan.service"
    _description = "Loan Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Code",
        default=lambda self: self.env["ir.sequence"].next_by_code("loan.service"),
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain="[('loan_applicant', '=', True)]",
    )
    id_number = fields.Char(
        string="Id Number", related="partner_id.id_number", readonly=True
    )
    date_of_application = fields.Date(string="Date of Application", required=True)
    payment_date = fields.Date(string="Payment Date", required=True)
    loan_amount = fields.Float(string="Loan Amount")
    daily_interest_rate = fields.Float(string="Daily Interest Rate")
    interest_amount = fields.Float(
        string="Interest Amount", compute="_compute_interest_amount", store=True
    )
    total_debt = fields.Float(
        string="Total Debt to Pay", compute="_compute_total_debt", store=True
    )
    state = fields.Selection(
        selection=[
            ("on_time", "On Time"),
            ("delayed", "Delayed"),
        ],
        string="State",
        default="on_time",
    )

    @api.depends(
        "loan_amount", "daily_interest_rate", "payment_date", "date_of_application"
    )
    def _compute_interest_amount(self):
        for record in self:
            if record.date_of_application and record.payment_date:
                days = (record.payment_date - record.date_of_application).days
                record.interest_amount = (
                    record.loan_amount * record.daily_interest_rate * days
                )

    @api.depends("loan_amount", "interest_amount")
    def _compute_total_debt(self):
        for record in self:
            record.total_debt = record.loan_amount + record.interest_amount

    def update_loan_status(self):
        today = date.today()
        loans = self.search([("state", "=", "on_time")])
        for loan in loans:
            if loan.payment_date and loan.payment_date < today:
                loan.state = "delayed"
