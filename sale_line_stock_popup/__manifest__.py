# -*- coding: utf-8 -*-
{
    "name": "Sale Line Stock Popup",
    "version": "18.0.1.1.0",
    "category": "Sales/Sales",
    "summary": "On Hand / Forecasted columns on Sales Order lines, plus a hover "
               "popup with image, prices and stock per warehouse and location.",
    "description": """
Sale Line Stock Popup
=====================
Hover the product name on any Sales Order line to open a rich card with the
product image, sales price, cost and a stock breakdown (On Hand, Forecasted or
both) for the order warehouse or for every warehouse of the company.

* On Hand / Forecasted columns on order lines (follow the metric setting,
  can be hidden or shown by each user from the optional columns menu).
* Per-company configuration in Sales settings (metric, scope).
* Database-wide master switch to deactivate the popup instantly.
* Asynchronous, cached OWL popover; works on editable and read-only lines.
* Server-side aggregation with read_group on quants and moves (constant number
  of queries whatever the number of warehouses).
* Arabic (ar_001) translation and RTL layout.
""",
    "author": "Ibrahim Yahia",
    "website": "https://www.linkedin.com/in/ibrahim-yahia",
    "license": "LGPL-3",
    "depends": ["sale_stock"],
    "data": [
        "data/ir_config_parameter_data.xml",
        "views/res_config_settings_views.xml",
        "views/sale_order_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_line_stock_popup/static/src/components/**/*",
        ],
        "web.assets_tests": [
            "sale_line_stock_popup/static/tests/tours/**/*",
        ],
    },
    "demo": ["demo/sale_line_stock_popup_demo.xml"],
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
