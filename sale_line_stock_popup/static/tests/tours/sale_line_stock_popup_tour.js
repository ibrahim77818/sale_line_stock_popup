/** @odoo-module **/

import { registry } from "@web/core/registry";

const TRIGGER = '.o_field_widget[name="order_line"] .o_data_row .o_sol_stock_popup_trigger:contains("Popup Tour Product")';

registry.category("web_tour.tours").add("sale_line_stock_popup_tour", {
    test: true,
    url: "/web",
    steps: () => [
        {
            content: "On Hand column is shown on the order line (metric = Both)",
            trigger: '.o_field_widget[name="order_line"] .o_data_row td[name="stock_popup_on_hand"]:contains(12)',
            run: function () {},
        },
        {
            content: "Forecasted column is shown too",
            trigger: '.o_field_widget[name="order_line"] th[data-name="stock_popup_forecast"]',
            run: function () {},
        },
        {
            content: "Hover the product of the order line",
            trigger: TRIGGER,
            run: function () {
                this.$anchor[0].dispatchEvent(new MouseEvent("mouseenter"));
            },
        },
        {
            content: "The card shows the order warehouse",
            trigger: '.o_sol_stock_popup_card .o_sol_stock_wh_current:contains("Tour Popup WH")',
            run: function () {},
        },
        {
            content: "On hand quantity is 12",
            trigger: ".o_sol_stock_popup_card .o_sol_stock_wh_current .o_sol_stock_on_hand:contains(12)",
            run: function () {},
        },
        {
            content: "Forecasted quantity is shown (metric = Both)",
            trigger: ".o_sol_stock_popup_card .o_sol_stock_wh_current .o_sol_stock_forecast",
            run: function () {},
        },
        {
            content: "Product details: image, sales price and cost (admin is Sales Administrator)",
            trigger: ".o_sol_stock_popup_card:has(.o_sol_stock_popup_image):has(.o_sol_stock_popup_price):has(.o_sol_stock_popup_cost)",
            run: function () {},
        },
        {
            content: "Leave the product",
            trigger: TRIGGER,
            run: function () {
                this.$anchor[0].dispatchEvent(new MouseEvent("mouseleave"));
            },
        },
        {
            content: "The card closes",
            trigger: "body:not(:has(.o_sol_stock_popup_card))",
            run: function () {},
        },
    ],
});
