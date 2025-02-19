from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

"""_Base model for Loan services_
"""


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
    date_of_application = fields.Date(
        string="Date of Application", default=fields.Date.context_today, required=True
    )
    payment_date = fields.Date(
        string="Payment Date",
        required=True,
        default=lambda self: self._get_default_payment_date(),
    )
    loan_amount = fields.Float(
        string="Loan Amount", help="You can request up to 1,000,000 of loan amount."
    )
    daily_interest_rate = fields.Float(
        string="Interest Rate",
        compute="_onchange_loan_amount",
        store=True)
    interest_amount = fields.Float(
        string="Interest Amount",
        help="The interest amount calculation per month",
        compute="_compute_interest_amount",
        store=True,
    )
    total_debt = fields.Float(
        string="Total Debt to Pay", compute="_compute_total_debt", store=True
    )
    # Feature
    remaining_debt = fields.Float(
        string=("Remaining Debt"), compute="_compute_remaining_debt", store=True
    )
    # Feature
    suggested_monthly_payment = fields.Float(
        string="Suggested Monthly Payment", compute="_compute_suggested_payment"
    )
    # Feature
    state = fields.Selection(
        selection=[
            ("on_time", "On Time"),
            ("delayed", "Delayed"),
            ("paid", "Paid"),
        ],
        string="State",
        default="on_time",
    )
    # Feature
    payment_ids = fields.One2many(
        string=("Payments"),
        comodel_name="loan.payment",
        inverse_name="loan_id",
    )

    """Set a default payment date based on loan amount categories."""

    # Feature
    def _get_default_payment_date(self):
        default_days = 30  # Default 1-month payment period
        if self.loan_amount:
            if self.loan_amount <= 1000:
                default_days = 7
            elif self.loan_amount <= 10000:
                default_days = 30
            elif self.loan_amount <= 100000:
                default_days = 365
            else:
                default_days = 3 * 365
        return fields.Date.context_today(self) + timedelta(days=default_days)

    # Feature

    @api.constrains("loan_amount")
    def _check_max_loan_amount(self):
        for record in self:
            if record.loan_amount > 1000000:
                raise ValidationError("The maximum allowed loan amount is 1,000,000.")

    # Feature

    @api.depends("loan_amount", "daily_interest_rate")
    def _onchange_loan_amount(self):
        for record in self:
            if record.loan_amount <= 1000:
                record.daily_interest_rate = 0.02
                record.payment_date = record.date_of_application + timedelta(days=7)
            elif record.loan_amount <= 10000:
                record.daily_interest_rate = 0.03
                record.payment_date = record.date_of_application + timedelta(days=30)
            elif record.loan_amount <= 100000:
                record.daily_interest_rate = 0.05
                record.payment_date = record.date_of_application + timedelta(
                    days=1 * 365
                )
            else:
                record.daily_interest_rate = 0.08
                record.payment_date = self.date_of_application + timedelta(
                    days=3 * 365
                )

    # Feature

    @api.constrains("partner_id", "loan_amount")
    def _check_total_debt(self):
        for record in self:
            total_debt = sum(
                self.search([("partner_id", "=", record.partner_id.id)]).mapped(
                    "total_debt"
                )
            )
            if total_debt >= 250000:
                raise ValidationError(
                    "You cannot apply for a new loan while your total debt exceeds 250,000."
                )

    # Feature (Removed time period from calculation)

    @api.depends(
        "loan_amount", "daily_interest_rate", "payment_date", "date_of_application"
    )
    def _compute_interest_amount(self):
        for record in self:
            if record.date_of_application and record.payment_date:
                months = (record.payment_date - record.date_of_application).days // 30
                record.interest_amount = (
                    record.loan_amount * record.daily_interest_rate * months
                )

    @api.depends("loan_amount", "interest_amount")
    def _compute_total_debt(self):
        for record in self:
            record.total_debt = record.loan_amount + record.interest_amount

    # Feature
    @api.depends("total_debt", "payment_ids.amount")
    def _compute_remaining_debt(self):
        for record in self:
            total_paid = sum(record.payment_ids.mapped("amount"))
            record.remaining_debt = record.total_debt - total_paid
            if record.remaining_debt <= 0:
                record.loan_amount = 0
                record.remaining_debt = 0
                record.state = "paid"

    # Feature
    @api.depends("total_debt", "date_of_application", "payment_date")
    def _compute_suggested_payment(self):
        for record in self:
            if record.date_of_application and record.payment_date:
                months = max(
                    (record.payment_date - record.date_of_application).days // 30, 1
                )
                record.suggested_monthly_payment = record.total_debt / months

    def update_loan_status(self):
        today = date.today()
        loans = self.search([("state", "=", "on_time")])
        for loan in loans:
            if loan.payment_date and loan.payment_date < today:
                loan.state = "delayed"
