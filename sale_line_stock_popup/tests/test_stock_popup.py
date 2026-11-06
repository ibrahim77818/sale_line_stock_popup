# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.tools import float_compare

from odoo.addons.sale_line_stock_popup.models.res_config_settings import GLOBAL_ACTIVE_PARAM
from .common import StockPopupCommon


@tagged("post_install", "-at_install")
class TestSaleLineStockPopup(StockPopupCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # WH A: 10.5 in stock + 4.25 on a shelf = 14.75 on hand
        cls._add_stock(cls.product, cls.wh_a.lot_stock_id, 10.5)
        cls._add_stock(cls.product, cls.shelf_a, 4.25)
        # WH B: 7 on hand
        cls._add_stock(cls.product, cls.wh_b.lot_stock_id, 7.0)
        # A -> customer 3 (out of A)
        cls._move(cls.product, cls.wh_a.lot_stock_id, cls.customers, 3.0)
        # supplier -> B 5 (into B)
        cls._move(cls.product, cls.suppliers, cls.wh_b.lot_stock_id, 5.0)
        # A -> B 2 (inter-warehouse: out of A, into B)
        cls._move(cls.product, cls.wh_a.lot_stock_id, cls.wh_b.lot_stock_id, 2.0)
        # A stock -> A shelf 1 (internal: no forecast impact)
        cls._move(cls.product, cls.wh_a.lot_stock_id, cls.shelf_a, 1.0)
        # draft move: must be ignored
        cls._move(cls.product, cls.wh_b.lot_stock_id, cls.customers, 100.0, confirm=False)

    # ------------------------------------------------------------------
    def assertQty(self, value, expected, msg=None):
        self.assertEqual(
            float_compare(value, expected, precision_rounding=self.product.uom_id.rounding), 0,
            msg or "%s != %s" % (value, expected),
        )

    def test_01_figures_match_odoo_per_warehouse(self):
        data = self._popup(warehouse_id=self.wh_a.id)
        self.assertTrue(data["enabled"])
        self.assertTrue(data["is_storable"])
        for wh, on_hand, forecast in ((self.wh_a, 14.75, 9.75), (self.wh_b, 7.0, 14.0)):
            row = self._row(data, wh)
            self.assertTrue(row, "warehouse %s missing" % wh.name)
            standard = self.product.with_context(warehouse=wh.id)
            self.assertQty(row["on_hand"], on_hand)
            self.assertQty(row["forecast"], forecast)
            self.assertQty(row["on_hand"], standard.qty_available)
            self.assertQty(row["forecast"], standard.virtual_available)

    def test_02_totals_are_sum_of_rows(self):
        data = self._popup(warehouse_id=self.wh_a.id)
        self.assertQty(data["totals"]["on_hand"], sum(r["on_hand"] for r in data["warehouses"]))
        self.assertQty(data["totals"]["forecast"], sum(r["forecast"] for r in data["warehouses"]))
        # our two warehouses hold everything for this new product
        self.assertQty(data["totals"]["on_hand"], 21.75)
        self.assertQty(data["totals"]["forecast"], 23.75)

    def test_03_scope_order_warehouse_only(self):
        self.company.sale_stock_popup_scope = "order_warehouse"
        data = self._popup(warehouse_id=self.wh_b.id)
        self.assertEqual([r["id"] for r in data["warehouses"]], [self.wh_b.id])
        self.assertTrue(data["warehouses"][0]["is_order_warehouse"])
        self.assertQty(data["warehouses"][0]["on_hand"], 7.0)

    def test_04_header_warehouse_change_is_followed(self):
        """Simulates the user changing the order warehouse before saving."""
        self.company.sale_stock_popup_scope = "order_warehouse"
        first = self._popup(warehouse_id=self.wh_a.id)
        second = self._popup(warehouse_id=self.wh_b.id)
        self.assertEqual(first["warehouses"][0]["id"], self.wh_a.id)
        self.assertEqual(second["warehouses"][0]["id"], self.wh_b.id)
        self.assertQty(first["warehouses"][0]["on_hand"], 14.75)
        self.assertQty(second["warehouses"][0]["on_hand"], 7.0)

    def test_05_order_warehouse_listed_first_in_all_scope(self):
        data = self._popup(warehouse_id=self.wh_b.id)
        self.assertEqual(data["warehouses"][0]["id"], self.wh_b.id)
        flagged = [r["id"] for r in data["warehouses"] if r["is_order_warehouse"]]
        self.assertEqual(flagged, [self.wh_b.id])

    def test_06_order_id_fallback(self):
        partner = self.env["res.partner"].create({"name": "Popup Customer"})
        order = self.env["sale.order"].create({
            "partner_id": partner.id,
            "warehouse_id": self.wh_b.id,
            "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1})],
        })
        self.company.sale_stock_popup_scope = "order_warehouse"
        data = self.env["product.product"].get_sale_line_stock_popup_data(
            self.product.id, order_id=order.id,
        )
        self.assertEqual([r["id"] for r in data["warehouses"]], [self.wh_b.id])

    def test_07_metric_flags(self):
        self.company.sale_stock_popup_metric = "on_hand"
        data = self._popup(warehouse_id=self.wh_a.id)
        self.assertTrue(data["show_on_hand"])
        self.assertFalse(data["show_forecast"])
        self.company.sale_stock_popup_metric = "forecast"
        data = self._popup(warehouse_id=self.wh_a.id)
        self.assertFalse(data["show_on_hand"])
        self.assertTrue(data["show_forecast"])

    def test_08_company_toggle_disables(self):
        self.company.sale_stock_popup_enabled = False
        data = self._popup(warehouse_id=self.wh_a.id)
        self.assertFalse(data["enabled"])
        self.assertNotIn("warehouses", data)

    def test_09_global_master_switch_disables(self):
        self.env["ir.config_parameter"].sudo().set_param(GLOBAL_ACTIVE_PARAM, False)
        self.assertFalse(self._popup(warehouse_id=self.wh_a.id)["enabled"])
        self.env["ir.config_parameter"].sudo().set_param(GLOBAL_ACTIVE_PARAM, "True")
        self.assertTrue(self._popup(warehouse_id=self.wh_a.id)["enabled"])

    def test_10_location_breakdown(self):
        data = self._popup(warehouse_id=self.wh_a.id)
        row = self._row(data, self.wh_a)
        by_id = {loc["id"]: loc["on_hand"] for loc in row["locations"]}
        self.assertQty(by_id[self.wh_a.lot_stock_id.id], 10.5)
        self.assertQty(by_id[self.shelf_a.id], 4.25)
        self.assertQty(sum(by_id.values()), row["on_hand"])

    def test_11_float_precision(self):
        product = self.env["product.product"].create({"name": "Precision", "type": "product"})
        shelf_2 = self.env["stock.location"].create({
            "name": "Popup Shelf 2", "usage": "internal", "location_id": self.wh_a.lot_stock_id.id,
        })
        self._add_stock(product, self.shelf_a, 0.1)
        self._add_stock(product, shelf_2, 0.2)
        row = self._row(self._popup(product=product, warehouse_id=self.wh_a.id), self.wh_a)
        # 0.1 + 0.2 must come back as exactly 0.3, not 0.30000000000000004
        self.assertEqual(row["on_hand"], 0.3)
        self.assertEqual(row["forecast"], 0.3)

    def test_12_non_storable_product(self):
        service = self.env["product.product"].create({"name": "Popup Service", "type": "service"})
        data = self._popup(product=service, warehouse_id=self.wh_a.id)
        self.assertTrue(data["enabled"])
        self.assertFalse(data["is_storable"])
        self.assertEqual(data["warehouses"], [])
        self.assertEqual(data["product"]["name"], service.display_name)

    def test_13_multi_company_isolation(self):
        company_2 = self.env["res.company"].create({"name": "Popup Company 2"})
        wh_other = self.env["stock.warehouse"].search([("company_id", "=", company_2.id)], limit=1)
        self.assertTrue(wh_other)
        self._add_stock(self.product, wh_other.lot_stock_id, 50.0)
        # a warehouse of another company passed from the client is ignored
        self.company.sale_stock_popup_scope = "order_warehouse"
        data = self._popup(warehouse_id=wh_other.id)
        self.assertNotEqual(data["warehouses"][0]["id"], wh_other.id)
        # all-warehouses scope never includes the other company
        self.company.sale_stock_popup_scope = "all_warehouses"
        data = self._popup(warehouse_id=self.wh_a.id)
        self.assertNotIn(wh_other.id, [r["id"] for r in data["warehouses"]])
        # a company outside the allowed companies falls back to the current one
        env = self.env(context=dict(self.env.context, allowed_company_ids=[self.company.id]))
        data = self._popup(env=env, company_id=company_2.id)
        self.assertEqual(data["company_id"], self.company.id)

    def test_14_salesman_without_inventory_rights(self):
        salesman = self.env["res.users"].create({
            "name": "Popup Salesman",
            "login": "popup_salesman",
            "company_id": self.company.id,
            "company_ids": [(6, 0, [self.company.id])],
            "groups_id": [(6, 0, [self.env.ref("sales_team.group_sale_salesman").id])],
        })
        data = self._popup(env=self.env(user=salesman), warehouse_id=self.wh_a.id)
        self.assertTrue(data["enabled"])
        self.assertQty(self._row(data, self.wh_a)["on_hand"], 14.75)
        self.assertFalse(data["product"]["show_cost"])
        self.assertFalse(data["product"]["cost"])

    def test_15_manager_sees_prices_and_cost(self):
        manager = self.env["res.users"].create({
            "name": "Popup Manager",
            "login": "popup_manager",
            "company_id": self.company.id,
            "company_ids": [(6, 0, [self.company.id])],
            "groups_id": [(6, 0, [self.env.ref("sales_team.group_sale_manager").id])],
        })
        data = self._popup(env=self.env(user=manager), warehouse_id=self.wh_a.id)
        self.assertTrue(data["product"]["show_cost"])
        self.assertIn("60", data["product"]["cost"])
        self.assertIn("100", data["product"]["sale_price"])
        self.assertEqual(data["product"]["default_code"], "POP-001")

    def test_16_query_count_independent_of_warehouse_count(self):
        """No N+1: adding warehouses must not add queries."""
        def count_queries():
            self._popup(warehouse_id=self.wh_a.id)  # warm ormcaches
            self.env.invalidate_all()
            before = self.cr.sql_log_count
            self._popup(warehouse_id=self.wh_a.id)
            return self.cr.sql_log_count - before

        baseline = count_queries()
        for i in range(4):
            wh = self.env["stock.warehouse"].create({
                "name": "Popup Extra %s" % i, "code": "PX%s" % i, "company_id": self.company.id,
            })
            self._add_stock(self.product, wh.lot_stock_id, 1.0 + i)
            self._move(self.product, wh.lot_stock_id, self.customers, 0.5)
        self.env.flush_all()
        self.assertLessEqual(count_queries(), baseline)

    # ------------------------------------------------------------------
    # Stock columns on sales order lines
    # ------------------------------------------------------------------
    def _order(self, warehouse, products):
        partner = self.env["res.partner"].create({"name": "Popup Column Customer"})
        return self.env["sale.order"].create({
            "partner_id": partner.id,
            "warehouse_id": warehouse.id,
            "order_line": [(0, 0, {"product_id": p.id, "product_uom_qty": 1}) for p in products],
        })

    def test_17_line_columns_order_warehouse(self):
        self.company.sale_stock_popup_scope = "order_warehouse"
        order = self._order(self.wh_a, self.product)
        line = order.order_line
        self.assertQty(line.stock_popup_on_hand, 14.75)
        self.assertQty(line.stock_popup_forecast, 9.75)
        # header warehouse change is reflected (non-stored compute)
        order.warehouse_id = self.wh_b
        self.assertQty(line.stock_popup_on_hand, 7.0)
        self.assertQty(line.stock_popup_forecast, 14.0)

    def test_18_line_columns_all_warehouses(self):
        self.company.sale_stock_popup_scope = "all_warehouses"
        line = self._order(self.wh_a, self.product).order_line
        self.assertQty(line.stock_popup_on_hand, 21.75)
        self.assertQty(line.stock_popup_forecast, 23.75)

    def test_19_column_visibility_follows_metric(self):
        order = self._order(self.wh_a, self.product)
        for metric, on_hand, forecast in (("both", True, True), ("on_hand", True, False),
                                          ("forecast", False, True)):
            self.company.sale_stock_popup_metric = metric
            order.invalidate_recordset(["stock_popup_show_on_hand", "stock_popup_show_forecast"])
            self.assertEqual(order.stock_popup_show_on_hand, on_hand, metric)
            self.assertEqual(order.stock_popup_show_forecast, forecast, metric)
        self.company.sale_stock_popup_enabled = False
        order.invalidate_recordset(["stock_popup_show_on_hand", "stock_popup_show_forecast"])
        self.assertFalse(order.stock_popup_show_on_hand)
        self.assertFalse(order.stock_popup_show_forecast)

    def test_20_line_columns_zero_for_service_and_when_disabled(self):
        service = self.env["product.product"].create({"name": "Popup Service 2", "type": "service"})
        order = self._order(self.wh_a, self.product | service)
        service_line = order.order_line.filtered(lambda l: l.product_id == service)
        self.assertEqual(service_line.stock_popup_on_hand, 0.0)
        self.company.sale_stock_popup_enabled = False
        order.order_line.invalidate_recordset(["stock_popup_on_hand", "stock_popup_forecast"])
        self.assertEqual(order.order_line.mapped("stock_popup_on_hand"), [0.0, 0.0])
