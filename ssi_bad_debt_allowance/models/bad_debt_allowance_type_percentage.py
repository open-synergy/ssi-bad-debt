# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class BadDebtAllowanceTypePercentage(models.Model):
    _name = "bad_debt_allowance_type.percentage"
    _description = "Bad Debt Allowance Type Percentage"

    type_id = fields.Many2one(
        string="Type",
        comodel_name="bad_debt_allowance_type",
        required=True,
        ondelete="cascade",
    )
    min_day_overdue = fields.Float(string="Min Day Overdue", required=True)
    max_day_overdue = fields.Float(string="Max Day Overdue", required=True)
    percentage = fields.Float(string="Percentage", required=True)
