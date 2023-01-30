# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from odoo.addons.ssi_decorator import ssi_decorator


class BadDebtAllowanceDetail(models.Model):
    _name = "bad_debt_allowance.detail"

    bad_debt_id = fields.Many2one(
        string="# Bad Debt",
        comodel_name="bad_debt_allowance",
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
    days_overdue = fields.Integer(string="Days Over Due", readonly=True)
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
    allowance_percentage = fields.Float(string="Allowance Percentage", required=True)
    amount_allowance = fields.Monetary(
        string="Amount Allowance",
        currency_field="company_currency_id",
        compute="_compute_allowance",
        store=True,
    )
    amount_allowance_currency = fields.Monetary(
        string="Amount Allowance Currency",
        currency_field="company_currency_id",
        compute="_compute_allowance",
        store=True,
    )
    allowance_move_line_id = fields.Many2one(
        string="Allowance Move Line",
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
        self.amount_residual = 0.0
        if self.source_move_line_id:
            self.amount_residual = self.source_move_line_id.amount_residual

    @api.onchange("source_move_line_id")
    def onchange_amount_residual_currency(self):
        self.amount_residual_currency = 0.0
        if self.source_move_line_id:
            self.amount_residual_currency = (
                self.source_move_line_id.amount_residual_currency
            )

    @api.onchange("source_move_line_id")
    def onchange_days_overdue(self):
        self.days_overdue = 0
        if self.source_move_line_id:
            self.days_overdue = self.source_move_line_id.days_overdue

    @api.onchange("source_move_line_id", "days_overdue")
    def onchange_percentage(self):
        self.percentage = 0.0

        domain = [
            ("type_id", "=", self.bad_debt_id.type_id),
            ("min_day_overdue", "<=", self.days_overdue),
            ("max_day_overdue", ">=", self.days_overdue),
        ]

        if self.source_move_line_id:
            type_percentages = self.env["bad_debt_allowance_type.percentage"].search(
                domain
            )
            if len(type_percentages) > 0:
                self.percentage = type_percentages[0].percentage

    @api.depends("allowance_percentage", "amount_residual", "amount_residual_currency")
    def _compute_allowance(self):
        for record in self:
            record.amount_allowance = (
                record.allowance_percentage / 100.00
            ) * record.amount_residual
            record.amount_allowance_currency = (
                record.allowance_percentage / 100.00
            ) * record.amount_residual_currency

    def _prepare_allowance_move(self, move):
        self.ensure_one()
        result = {
            "move_id": move.id,
            "name": "Bad Debt Allowance for ${self.source_move_line_id.move_id.name}",
            "account_id": self.allowance_account_id.id,
            "debit": 0.0,
            "credit": self.amount_allowance,
            "currency_id": self.company_currency_id.id,
            "amount_currency": self.amount_allowance_currency,
        }
        return result

    def _prepare_expense_move(self, move):
        self.ensure_one()
        result = {
            "move_id": move.id,
            "name": "Bad Debt Allowance for ${self.source_move_line_id.move_id.name}",
            "account_id": self.expense_account_id.id,
            "credit": 0.0,
            "debit": self.amount_allowance,
            "currency_id": self.company_currency_id.id,
            "amount_currency": self.amount_allowance_currency,
        }
        return result

    @ssi_decorator.post_done_action()
    def _create_accounting_entry(self, move):
        self.ensure_one()
        allowance_move_line = self.env["account.move.line"].create(
            self._prepare_allowance_move(move)
        )
        expense_move_line = self.env["account.move.line"].create(
            self._prepare_expense_move(move)
        )
        self.write(
            {
                "allowance_move_line_id": allowance_move_line.id,
                "expense_move_line_id": expense_move_line.id,
            }
        )

    def _reconcile(self):
        moves = self.source_move_line_id + self.allowance_move_line_id
        moves.reconcile()

    def _unreconcile(self):
        moves = self.source_move_line_id + self.allowance_move_line_id
        moves.remove_move_reconcile()
