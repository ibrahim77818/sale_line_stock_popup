/** @odoo-module **/

import { Component } from "@odoo/owl";
import { formatFloat } from "@web/views/fields/formatters";

export class StockPopupCard extends Component {
    get data() {
        return this.props.data || {};
    }

    get hasStockTable() {
        return this.data.is_storable && (this.data.warehouses || []).length > 0;
    }

    get showTotals() {
        return (this.data.warehouses || []).length > 1;
    }

    formatQty(value) {
        return formatFloat(value || 0, { digits: [false, this.data.precision || 2] });
    }

    qtyClass(value) {
        if (value < 0) {
            return "text-danger fw-bold";
        }
        return value === 0 ? "text-muted" : "";
    }

    onMouseEnter() {
        if (this.props.onMouseEnter) {
            this.props.onMouseEnter();
        }
    }

    onMouseLeave() {
        if (this.props.onMouseLeave) {
            this.props.onMouseLeave();
        }
    }
}
StockPopupCard.template = "sale_line_stock_popup.StockPopupCard";
