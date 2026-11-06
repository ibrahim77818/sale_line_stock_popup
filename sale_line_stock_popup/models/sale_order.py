# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Drive the visibility of the stock columns on the order lines.
    stock_popup_show_on_hand = fields.Boolean(compute="_compute_stock_popup_columns")
    stock_popup_show_forecast = fields.Boolean(compute="_compute_stock_popup_columns")

    @api.depends("company_id")
    def _compute_stock_popup_columns(self):
        Product = self.env["product.product"]
        for order in self:
            company = order.company_id or self.env.company
            active = Product._sale_stock_popup_is_active(company)
            metric = company.sudo().sale_stock_popup_metric
            order.stock_popup_show_on_hand = active and metric in ("on_hand", "both")
            order.stock_popup_show_forecast = active and metric in ("forecast", "both")


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    stock_popup_on_hand = fields.Float(
        string="On Hand",
        compute="_compute_stock_popup_qty",
        digits="Product Unit of Measure",
        help="Quantity on hand in the product unit of measure, for the warehouse "
             "scope set in Sales settings.",
    )
    stock_popup_forecast = fields.Float(
        string="Forecasted",
        compute="_compute_stock_popup_qty",
        digits="Product Unit of Measure",
        help="Forecasted quantity in the product unit of measure, for the warehouse "
             "scope set in Sales settings.",
    )

    @api.depends("product_id", "display_type", "order_id.warehouse_id", "order_id.company_id")
    def _compute_stock_popup_qty(self):
        """Batched: one quantity computation per (company, warehouse set),
        not one per line."""
        Product = self.env["product.product"]
        Warehouse = self.env["stock.warehouse"].sudo()
        company_whs = {}
        groups = defaultdict(lambda: self.env["sale.order.line"])
        for line in self:
            line.stock_popup_on_hand = 0.0
            line.stock_popup_forecast = 0.0
            if line.display_type or not line.product_id or line.product_id.type != "product":
                continue
            company = line.order_id.company_id or self.env.company
            if not Product._sale_stock_popup_is_active(company):
                continue
            if company.id not in company_whs:
                company_whs[company.id] = tuple(
                    Warehouse.search([("company_id", "=", company.id)], order="sequence, id").ids
                )
            if company.sudo().sale_stock_popup_scope == "all_warehouses":
                wh_ids = company_whs[company.id]
            else:
                order_wh = line.order_id.warehouse_id
                if order_wh and order_wh.company_id == company:
                    wh_ids = (order_wh.id,)
                else:
                    wh_ids = company_whs[company.id][:1]
            if wh_ids:
                groups[(company.id, wh_ids)] |= line
        for (company_id, wh_ids), lines in groups.items():
            products = lines.product_id.sudo().with_company(company_id).with_context(
                warehouse=list(wh_ids),
            )
            qties = {p.id: (p.qty_available, p.virtual_available) for p in products}
            for line in lines:
                line.stock_popup_on_hand, line.stock_popup_forecast = qties[line.product_id.id]
