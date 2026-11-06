# Sale Line Stock Popup (Odoo 16.0)

**On Hand / Forecasted stock on Sales Order lines, plus a hover card with image, prices and stock per warehouse and location.**

Odoo 16.0 · Community & Enterprise · English & Arabic (RTL) · LGPL-3

## Features

- **Stock columns on order lines** – *On Hand* and *Forecasted*, shown according to the *Metric* setting. Each user can hide or show them from the optional columns menu. Negative figures turn red.
- **Hover card** – rest the mouse on a line's product to see its image, internal reference, sales price, cost (Sales Administrators only) and a stock breakdown per warehouse, with the internal locations under each and a total.
- **Scope** – the order's warehouse only, or every warehouse of the company. Figures follow the order header live, before saving.
- **Forecast like Odoo** – on hand + incoming − outgoing from waiting / confirmed / reserved moves; inter-warehouse moves count on both sides, moves inside one warehouse are ignored.
- **Fast** – the card uses 3 queries whatever the number of warehouses; columns compute stock once per warehouse set, not per line; results cached 30 s in the browser.
- **Safe** – salespeople see stock without Inventory rights; only warehouses of the order's (allowed) company are counted.
- **Arabic (ar_001)** translation and right-to-left layout.

## Configuration

*Sales › Configuration › Settings › Order Line Stock Popup*

| Setting | Values |
|---|---|
| Stock on SO lines (per company) | on / off (default off) |
| Metric | Quantity On Hand · Forecasted Quantity · Both |
| Scope | Sales Order Warehouse · All Warehouses |
| Popup Active (All Companies) | database-wide master switch (default on) |

## Installation

1. Copy the `sale_line_stock_popup` folder of this branch into your addons path.
2. Update the apps list and install **Sale Line Stock Popup** (depends on `sale_stock`).
3. Enable it in Sales settings.

Demo data (two warehouses, three products, an outgoing order, an incoming receipt and a quotation) loads in databases with demo data.

## Tests

20 `TransactionCase` tests and 1 browser tour:

```bash
odoo-bin -d <db> -i sale_line_stock_popup --test-tags /sale_line_stock_popup --stop-after-init
```

## Branches

| Branch | Odoo version |
|---|---|
| `16.0` | 16.0 (default) |
| `17.0` | 17.0 |
| `18.0` | 18.0 |
| `19.0` | 19.0 |

Version notes for this branch: Uses `attrs` view syntax, `product.type == 'product'` for stocked products.

## Author

**Ibrahim Yahia** · [LinkedIn](https://www.linkedin.com/in/ibrahim-yahia) · ibrahim.yahiah@gmail.com

License: LGPL-3
