# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class BadDebtAllowanceType(models.Model):
    _name = "bad_debt_allowance_type"
    _description = "Bad Debt Allowance Type"
    _inherit = ["mixin.master_data"]

    min_days_due = fields.Integer(string="Min Days Due", required=True)
    max_days_due = fields.Integer(string="Max Days Due", required=True)
    journal_id = fields.Many2one(
        string="Journal", comodel_name="account.journal", ondelete="restrict"
    )
    allowance_account_id = fields.Many2one(
        string="Allowance Account",
        comodel_name="account.account",
        ondelete="restrict",
    )
    expense_account_id = fields.Many2one(
        string="Expense Account",
        comodel_name="account.account",
        ondelete="restrict",
    )
    allowed_account_ids = fields.Many2many(
        string="Allowed Accounts",
        comodel_name="account.account",
        relation="rel_bad_debt_allowance_type_2_account",
        column1="type_id",
        column2="account_id",
    )
    percentage_ids = fields.One2many(
        string="Percentages",
        comodel_name="bad_debt_allowance_type.percentage",
        inverse_name="type_id",
    )
    use_min_days_due = fields.Boolean(
        string="Use Min Days Due",
    )
    use_max_days_due = fields.Boolean(
        string="Use Max Days Due",
    )
