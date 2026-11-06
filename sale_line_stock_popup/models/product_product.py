# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, models
from odoo.tools import float_round, format_amount

from .res_config_settings import GLOBAL_ACTIVE_PARAM

# Same states Odoo uses for incoming/outgoing quantities in the forecast.
FORECAST_MOVE_STATES = ("waiting", "confirmed", "assigned", "partially_available")
MAX_LOCATIONS_PER_WAREHOUSE = 6


class ProductProduct(models.Model):
    _inherit = "product.product"

    # ------------------------------------------------------------------
    # Public RPC entry point (called by the OWL hover widget)
    # ------------------------------------------------------------------
    @api.model
    def get_sale_line_stock_popup_data(self, product_id, warehouse_id=False,
                                       company_id=False, order_id=False):
        """Return everything the hover card needs in one round trip.

        ``warehouse_id`` and ``company_id`` come from the (possibly unsaved)
        sales order header so the popup follows header changes immediately;
        ``order_id`` is only a fallback when they are not provided.
        """
        company = self._sale_stock_popup_company(company_id, order_id)
        if not self._sale_stock_popup_is_active(company):
            return {"enabled": False, "company_id": company.id}

        product = self.browse(int(product_id)).exists()
        if not product:
            return {"enabled": True, "company_id": company.id, "product": False}
        # The user must be allowed to see the product; stock figures are then
        # read with sudo so salespeople without Inventory rights get them too.
        product.check_access_rights("read")
        product.check_access_rule("read")
        product = product.with_company(company)

        if not warehouse_id and order_id:
            order = self.env["sale.order"].browse(int(order_id)).exists()
            if order:
                order.check_access_rights("read")
                order.check_access_rule("read")
                warehouse_id = order.warehouse_id.id

        settings = company.sudo()
        metric = settings.sale_stock_popup_metric or "both"
        scope = settings.sale_stock_popup_scope or "order_warehouse"
        warehouses, current = self._sale_stock_popup_warehouses(company, scope, warehouse_id)

        uom = product.uom_id
        precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        is_storable = product.type == "product"
        rows = []
        totals = {"on_hand": 0.0, "forecast": 0.0}
        if is_storable and warehouses:
            rows = self._sale_stock_popup_aggregate(product, warehouses, current)
            for row in rows:
                totals["on_hand"] += row["on_hand"]
                totals["forecast"] += row["forecast"]
            totals = {k: float_round(v, precision_rounding=uom.rounding) for k, v in totals.items()}

        return {
            "enabled": True,
            "company_id": company.id,
            "metric": metric,
            "scope": scope,
            "show_on_hand": metric in ("on_hand", "both"),
            "show_forecast": metric in ("forecast", "both"),
            "precision": precision,
            "is_storable": is_storable,
            "product": self._sale_stock_popup_product_info(product, company),
            "warehouses": rows,
            "totals": totals,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @api.model
    def _sale_stock_popup_company(self, company_id, order_id=False):
        allowed = self.env.companies
        if company_id:
            company = self.env["res.company"].browse(int(company_id))
            if company in allowed:
                return company
        if order_id:
            order = self.env["sale.order"].browse(int(order_id)).exists()
            if order and order.company_id in allowed:
                return order.company_id
        return self.env.company

    @api.model
    def _sale_stock_popup_is_active(self, company):
        param = self.env["ir.config_parameter"].sudo().get_param(GLOBAL_ACTIVE_PARAM)
        global_active = str(param).strip().lower() in ("1", "true", "yes")
        return bool(global_active and company.sudo().sale_stock_popup_enabled)

    @api.model
    def _sale_stock_popup_warehouses(self, company, scope, warehouse_id):
        """Return (warehouses in scope, warehouse of the order)."""
        Warehouse = self.env["stock.warehouse"].sudo()
        order_wh = Warehouse.browse(int(warehouse_id)).exists() if warehouse_id else Warehouse
        if order_wh and order_wh.company_id != company:
            order_wh = Warehouse
        company_whs = Warehouse.search([("company_id", "=", company.id)], order="sequence, id")
        if not order_wh:
            order_wh = company_whs[:1]
        if scope == "all_warehouses":
            return company_whs, order_wh
        return order_wh, order_wh

    @api.model
    def _sale_stock_popup_location_map(self, warehouses):
        """Map every location under the warehouses' view locations to its
        warehouse, using parent_path (one query, no computed field)."""
        view_to_wh = {wh.view_location_id.id: wh.id for wh in warehouses}
        locations = self.env["stock.location"].sudo().search_read(
            [("id", "child_of", list(view_to_wh))], ["parent_path"],
        )
        loc_wh = {}
        for loc in locations:
            for part in (loc["parent_path"] or "").split("/"):
                if part and int(part) in view_to_wh:
                    loc_wh[loc["id"]] = view_to_wh[int(part)]
                    break
        return loc_wh

    @api.model
    def _sale_stock_popup_aggregate(self, product, warehouses, current):
        """Constant number of queries whatever the number of warehouses:
        one location search, one quant read_group, one move read_group."""
        loc_wh = self._sale_stock_popup_location_map(warehouses)
        location_ids = list(loc_wh)
        rounding = product.uom_id.rounding

        on_hand = defaultdict(float)
        per_location = defaultdict(list)
        quant_groups = self.env["stock.quant"].sudo().read_group(
            [("product_id", "=", product.id), ("location_id", "in", location_ids)],
            ["location_id", "quantity:sum"], ["location_id"], lazy=False,
        )
        for group in quant_groups:
            loc_id, loc_name = group["location_id"]
            wh_id = loc_wh.get(loc_id)
            qty = group["quantity"] or 0.0
            if not wh_id:
                continue
            on_hand[wh_id] += qty
            if float_round(qty, precision_rounding=rounding):
                per_location[wh_id].append({
                    "id": loc_id,
                    "name": loc_name,
                    "on_hand": float_round(qty, precision_rounding=rounding),
                })

        incoming = defaultdict(float)
        outgoing = defaultdict(float)
        move_groups = self.env["stock.move"].sudo().read_group(
            [
                ("product_id", "=", product.id),
                ("state", "in", FORECAST_MOVE_STATES),
                "|",
                ("location_id", "in", location_ids),
                ("location_dest_id", "in", location_ids),
            ],
            ["location_id", "location_dest_id", "product_qty:sum"],
            ["location_id", "location_dest_id"], lazy=False,
        )
        for group in move_groups:
            src_wh = loc_wh.get(group["location_id"] and group["location_id"][0])
            dst_wh = loc_wh.get(group["location_dest_id"] and group["location_dest_id"][0])
            if src_wh == dst_wh:
                continue  # internal move inside one warehouse: no impact
            qty = group["product_qty"] or 0.0
            if dst_wh:
                incoming[dst_wh] += qty
            if src_wh:
                outgoing[src_wh] += qty

        rows = []
        for wh in warehouses:
            locations = sorted(per_location[wh.id], key=lambda loc: loc["name"] or "")
            rows.append({
                "id": wh.id,
                "name": wh.name,
                "code": wh.code,
                "is_order_warehouse": wh == current,
                "on_hand": float_round(on_hand[wh.id], precision_rounding=rounding),
                "incoming": float_round(incoming[wh.id], precision_rounding=rounding),
                "outgoing": float_round(outgoing[wh.id], precision_rounding=rounding),
                "forecast": float_round(
                    on_hand[wh.id] + incoming[wh.id] - outgoing[wh.id],
                    precision_rounding=rounding,
                ),
                "locations": locations[:MAX_LOCATIONS_PER_WAREHOUSE],
                "more_locations": max(len(locations) - MAX_LOCATIONS_PER_WAREHOUSE, 0),
            })
        # Order warehouse first, then the configured warehouse sequence.
        rows.sort(key=lambda r: not r["is_order_warehouse"])
        return rows

    @api.model
    def _sale_stock_popup_product_info(self, product, company):
        currency = company.currency_id
        show_cost = self.env.user.has_group("sales_team.group_sale_manager")
        unique = product.write_date and product.write_date.strftime("%Y%m%d%H%M%S") or ""
        return {
            "id": product.id,
            "name": product.display_name,
            "default_code": product.default_code or "",
            "image_url": "/web/image/product.product/%s/image_128?unique=%s" % (product.id, unique),
            "uom": product.uom_id.name,
            "sale_price": format_amount(self.env, product.lst_price, currency),
            "show_cost": show_cost,
            "cost": format_amount(self.env, product.sudo().standard_price, currency) if show_cost else False,
        }
