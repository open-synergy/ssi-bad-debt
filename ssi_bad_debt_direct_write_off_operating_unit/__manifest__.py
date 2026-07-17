# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Bad Debt Direct Write Off + Operating Unit",
    "version": "14.0.1.0.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "ssi_bad_debt_direct_write_off",
        "ssi_operating_unit_mixin",
    ],
    "data": [
        "security/res_group/bad_debt_direct_write_off.xml",
        "security/ir_rule/bad_debt_direct_write_off.xml",
        "view/bad_debt_direct_write_off.xml",
    ],
}
