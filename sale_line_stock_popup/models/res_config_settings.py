# -*- coding: utf-8 -*-
from odoo import fields, models

GLOBAL_ACTIVE_PARAM = "sale_line_stock_popup.global_active"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_stock_popup_enabled = fields.Boolean(
        related="company_id.sale_stock_popup_enabled", readonly=False,
    )
    sale_stock_popup_metric = fields.Selection(
        related="company_id.sale_stock_popup_metric", readonly=False,
    )
    sale_stock_popup_scope = fields.Selection(
        related="company_id.sale_stock_popup_scope", readonly=False,
    )
    sale_stock_popup_global_active = fields.Boolean(
        string="Popup Active (All Companies)",
        config_parameter=GLOBAL_ACTIVE_PARAM,
        help="Master switch for the whole database. Turn it off to deactivate "
             "the hover popup everywhere without losing the configuration.",
    )
