# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class BadDebtDirectWriteOffType(models.Model):
    _name = "bad_debt_direct_write_off_type"
    _description = "Bad Debt Write Off Type"
    _inherit = ["mixin.master_data"]

    use_min_days_due = fields.Boolean(
        string="Use Min Days Due",
    )
    min_days_due = fields.Integer(
        string="Min Days Due",
    )
    use_max_days_due = fields.Boolean(
        string="Use Max Days Due",
    )
    max_days_due = fields.Integer(
        string="Max Days Due",
    )
    journal_id = fields.Many2one(
        string="Journal", comodel_name="account.journal", ondelete="restrict"
    )
    expense_account_id = fields.Many2one(
        string="Expense Account",
        comodel_name="account.account",
        ondelete="restrict",
    )
    allowed_account_ids = fields.Many2many(
        string="Allowed Accounts",
        comodel_name="account.account",
        relation="rel_bad_debt_type_2_account",
        column1="type_id",
        column2="account_id",
    )
