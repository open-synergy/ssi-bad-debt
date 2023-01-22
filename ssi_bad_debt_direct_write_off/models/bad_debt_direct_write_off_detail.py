# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class BadDebtDirectWriteOffDetail(models.Model):
    _name = "bad_debt_direct_write_off.detail"

    bad_debt_id = fields.Many2one(
        string="# Bad Debt",
        comodel_name="bad_debt_direct_write_off",
        required=True,
        ondelete="cascade",
    )
    source_move_line_id = fields.Many2one(
        string="# Source Move Line",
        comodel_name="account.move.line",
        required=True,
        ondelete="restrict",
    )
    date = fields.Date(string="Date", related="source_move_line_id.date", store=True)
    date_due = fields.Date(
        string="Date Due", related="source_move_line_id.date_maturity", store=True
    )
    day_due = fields.Integer(
        string="Day Due", related="source_move_line_id.days_overdue", store=True
    )
    company_currency_id = fields.Many2one(
        string="Company Currency", related="source_move_line_id.company_currency_id"
    )
    amount = fields.Monetary(
        string="Amount",
        currency_field="company_currency_id",
        related="source_move_line_id.balance",
    )
    amount_currency = fields.Monetary(
        string="Amount Currency",
        currency_field="company_currency_id",
        related="source_move_line_id.amount_currency",
        store=True,
    )
    amount_residual = fields.Monetary(
        string="Amount Residual", currency_field="company_currency_id", readonly=True
    )
    amount_residual_currency = fields.Monetary(
        string="Amount Residual Currency",
        currency_field="company_currency_id",
        readonly=True,
    )
    receivable_move_line_id = fields.Many2one(
        string="# Receivable Move Line",
        comodel_name="account.move.line",
        readonly=True,
        ondelete="restrict",
    )
    expense_move_line_id = fields.Many2one(
        string="# Expense Move Line",
        comodel_name="account.move.line",
        readonly=True,
        ondelete="restrict",
    )

    @api.onchange("source_move_line_id")
    def onchange_amount_residual(self):
        if self.source_move_line_id:
            self.amount_residual = self.source_move_line_id.amount_residual

    @api.onchange("source_move_line_id")
    def onchange_amount_residual_currency(self):
        if self.source_move_line_id:
            self.amount_residual_currency = (
                self.source_move_line_id.amount_residual_currency
            )
