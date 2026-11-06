/** @odoo-module **/

import { onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { SaleOrderLineProductField } from "@sale/js/sale_product_field";
import { StockPopupCard } from "./stock_popup_card";
import { fetchStockPopupData, isStockPopupDisabled } from "./stock_popup_service";

const OPEN_DELAY = 350;
const CLOSE_DELAY = 250;

const m2oId = (value) => (Array.isArray(value) ? value[0] : value) || false;

/**
 * Extends the standard sales order line product field (sol_product_many2one)
 * so everything it does (configurator, matrix, combo...) keeps working, and
 * wraps it in a hover zone that opens the stock card in a popover.
 */
export class SolStockPopupProductField extends SaleOrderLineProductField {
    setup() {
        super.setup();
        this.stockPopupOrm = useService("orm");
        this.stockPopover = usePopover();
        this.stockPopupAnchor = useRef("stockPopupAnchor");
        this.stockPopupState = { openTimer: null, closeTimer: null, close: null, token: 0 };
        onWillUnmount(() => this.closeStockPopup());
    }

    /** Values are read live from the (possibly unsaved) order header. */
    get stockPopupParams() {
        const record = this.props.record;
        const root = record.model && record.model.root;
        const order = root && root.resModel === "sale.order" ? root : null;
        return {
            // product_template_id column (configurator) -> use the variant
            productId: m2oId(record.data.product_id),
            warehouseId: order ? m2oId(order.data.warehouse_id) : false,
            companyId: order ? m2oId(order.data.company_id) : false,
            orderId: order && order.resId ? order.resId : false,
        };
    }

    onStockPopupEnter() {
        const state = this.stockPopupState;
        clearTimeout(state.closeTimer);
        if (state.close) {
            return; // already open
        }
        const params = this.stockPopupParams;
        if (!params.productId || isStockPopupDisabled(params.companyId)) {
            return;
        }
        const anchor = this.stockPopupAnchor.el;
        if (anchor && anchor.querySelector(".o-autocomplete--dropdown-menu")) {
            return; // the user is picking a product: don't cover the dropdown
        }
        clearTimeout(state.openTimer);
        const token = ++state.token;
        state.openTimer = setTimeout(async () => {
            let data = null;
            let error = false;
            try {
                data = await fetchStockPopupData(this.stockPopupOrm, params);
            } catch {
                error = true;
            }
            const el = this.stockPopupAnchor.el;
            if (token !== state.token || !el || !el.isConnected || state.close) {
                return; // mouse left, row re-rendered or popup already shown
            }
            if (!error && (!data || !data.enabled || !data.product)) {
                return;
            }
            this.openStockPopup(el, data, error);
        }, OPEN_DELAY);
    }

    onStockPopupLeave() {
        const state = this.stockPopupState;
        state.token++; // cancel a pending open
        clearTimeout(state.openTimer);
        this.scheduleStockPopupClose();
    }

    openStockPopup(target, data, error) {
        const state = this.stockPopupState;
        state.close = this.stockPopover.add(
            target,
            StockPopupCard,
            {
                data,
                error,
                onMouseEnter: () => clearTimeout(state.closeTimer),
                onMouseLeave: () => this.scheduleStockPopupClose(),
            },
            {
                position: "bottom",
                popoverClass: "o_sol_stock_popover",
                onClose: () => {
                    state.close = null;
                },
            }
        );
    }

    scheduleStockPopupClose() {
        const state = this.stockPopupState;
        clearTimeout(state.closeTimer);
        state.closeTimer = setTimeout(() => this.closeStockPopup(), CLOSE_DELAY);
    }

    closeStockPopup() {
        const state = this.stockPopupState;
        state.token++;
        clearTimeout(state.openTimer);
        clearTimeout(state.closeTimer);
        if (state.close) {
            const close = state.close;
            state.close = null;
            close();
        }
    }
}
SolStockPopupProductField.template = "sale_line_stock_popup.ProductField";

registry.category("fields").add("sol_stock_popup_product", SolStockPopupProductField);
