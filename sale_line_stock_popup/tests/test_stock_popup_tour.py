# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged

from odoo.addons.sale_line_stock_popup.models.res_config_settings import GLOBAL_ACTIVE_PARAM


@tagged("post_install", "-at_install")
class TestSaleLineStockPopupTour(HttpCase):

    def test_stock_popup_hover_tour(self):
        company = self.env.ref("base.main_company")
        company.write({
            "sale_stock_popup_enabled": True,
            "sale_stock_popup_metric": "both",
            "sale_stock_popup_scope": "order_warehouse",
        })
        self.env["ir.config_parameter"].sudo().set_param(GLOBAL_ACTIVE_PARAM, "True")

        warehouse = self.env["stock.warehouse"].create({
            "name": "Tour Popup WH", "code": "TPW", "company_id": company.id,
        })
        product = self.env["product.product"].create({
            "name": "Popup Tour Product",
            "type": "consu",
            "is_storable": True,
            "list_price": 25.0,
            "standard_price": 10.0,
        })
        self.env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, 12.0)
        partner = self.env["res.partner"].create({"name": "Popup Tour Customer"})
        order = self.env["sale.order"].create({
            "partner_id": partner.id,
            "company_id": company.id,
            "warehouse_id": warehouse.id,
            "order_line": [(0, 0, {"product_id": product.id, "product_uom_qty": 2})],
        })
        self.start_tour(
            "/odoo/sales/%s" % order.id,
            "sale_line_stock_popup_tour",
            login="admin",
        )
