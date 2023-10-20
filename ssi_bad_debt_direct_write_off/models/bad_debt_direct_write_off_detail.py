# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class BadDebtDirectWriteOffDetail(models.Model):
    _name = "bad_debt_direct_write_off.detail"
    _description = "Bad Debt Write Off - Detail"

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
        ondelete="set null",
    )
    expense_move_line_id = fields.Many2one(
        string="# Expense Move Line",
        comodel_name="account.move.line",
        readonly=True,
        ondelete="set null",
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

    def _create_account_move_line(self):
        self.ensure_one()
        ML = self.env["account.move.line"].with_context(check_move_validity=False)
        expense_line = ML.create(self._prepare_expense_move_line_data())
        receivable_line = ML.create(self._prepare_receivable_move_line_data())
        self.write(
            {
                "expense_move_line_id": expense_line.id,
                "receivable_move_line_id": receivable_line.id,
            }
        )

    def _prepare_expense_move_line_data(self):
        self.ensure_one()
        name = "Bad debt %s" % (self.source_move_line_id.move_id.name)
        data = {
            "move_id": self.bad_debt_id.move_id.id,
            "account_id": self.bad_debt_id.expense_account_id.id,
            "name": name,
            "debit": self.amount_residual,
            "credit": 0,
            "currency_id": self.source_move_line_id.currency_id.id,
            "amount_currency": self.amount_residual_currency,
        }
        return data

    def _prepare_receivable_move_line_data(self):
        self.ensure_one()
        name = "Bad debt %s" % (self.source_move_line_id.move_id.name)
        data = {
            "move_id": self.bad_debt_id.move_id.id,
            "account_id": self.source_move_line_id.account_id.id,
            "name": name,
            "credit": self.amount_residual,
            "debit": 0,
            "currency_id": self.source_move_line_id.currency_id.id,
            "amount_currency": self.amount_residual_currency,
        }
        return data

    def _reconcile(self):
        self.ensure_one()
        moves = self.source_move_line_id + self.receivable_move_line_id
        moves.reconcile()

    def _unreconcile(self):
        moves = self.source_move_line_id + self.receivable_move_line_id
        moves.remove_move_reconcile()
