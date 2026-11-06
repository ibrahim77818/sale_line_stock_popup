# -*- coding: utf-8 -*-
from odoo import fields, models

STOCK_POPUP_METRICS = [
    ("on_hand", "Quantity On Hand"),
    ("forecast", "Forecasted Quantity"),
    ("both", "Both"),
]
STOCK_POPUP_SCOPES = [
    ("order_warehouse", "Sales Order Warehouse"),
    ("all_warehouses", "All Warehouses"),
]


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_stock_popup_enabled = fields.Boolean(
        string="Stock on SO lines",
        default=False,
        help="Show On Hand / Forecasted columns on sales order lines and a stock popup when hovering the line product.",
    )
    sale_stock_popup_metric = fields.Selection(
        STOCK_POPUP_METRICS,
        string="Stock Popup Metric",
        default="both",
        required=True,
        help="Quantities displayed in the stock popup.",
    )
    sale_stock_popup_scope = fields.Selection(
        STOCK_POPUP_SCOPES,
        string="Stock Popup Scope",
        default="order_warehouse",
        required=True,
        help="Warehouses included in the stock popup.",
    )
