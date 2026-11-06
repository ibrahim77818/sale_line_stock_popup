# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from odoo.addons.sale_line_stock_popup.models.res_config_settings import GLOBAL_ACTIVE_PARAM


class StockPopupCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.company.write({
            "sale_stock_popup_enabled": True,
            "sale_stock_popup_metric": "both",
            "sale_stock_popup_scope": "all_warehouses",
        })
        cls.env["ir.config_parameter"].sudo().set_param(GLOBAL_ACTIVE_PARAM, "True")

        Warehouse = cls.env["stock.warehouse"]
        cls.wh_a = Warehouse.create({"name": "Popup WH A", "code": "PWA", "company_id": cls.company.id})
        cls.wh_b = Warehouse.create({"name": "Popup WH B", "code": "PWB", "company_id": cls.company.id})
        cls.shelf_a = cls.env["stock.location"].create({
            "name": "Popup Shelf",
            "usage": "internal",
            "location_id": cls.wh_a.lot_stock_id.id,
        })
        cls.customers = cls.env.ref("stock.stock_location_customers")
        cls.suppliers = cls.env.ref("stock.stock_location_suppliers")

        cls.product = cls.env["product.product"].create({
            "name": "Popup Product",
            "type": "consu",
            "is_storable": True,
            "default_code": "POP-001",
            "list_price": 100.0,
            "standard_price": 60.0,
        })

    @classmethod
    def _add_stock(cls, product, location, qty):
        cls.env["stock.quant"]._update_available_quantity(product, location, qty)

    @classmethod
    def _move(cls, product, src, dst, qty, confirm=True):
        move = cls.env["stock.move"].create({
            "name": "Popup test move",
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": qty,
            "location_id": src.id,
            "location_dest_id": dst.id,
            "company_id": cls.company.id,
        })
        if confirm:
            move._action_confirm()
        return move

    def _popup(self, product=None, env=None, **kwargs):
        env = env or self.env
        kwargs.setdefault("company_id", self.company.id)
        return env["product.product"].get_sale_line_stock_popup_data(
            (product or self.product).id, **kwargs
        )

    @staticmethod
    def _row(data, warehouse):
        rows = [r for r in data["warehouses"] if r["id"] == warehouse.id]
        return rows[0] if rows else None
