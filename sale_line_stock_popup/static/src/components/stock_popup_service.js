/** @odoo-module **/

/**
 * Small client-side cache in front of the stock popup RPC.
 *  - identical hovers within CACHE_TTL reuse the same promise (no duplicate RPC,
 *    concurrent hovers on the same product share one request);
 *  - the cache key contains the header warehouse/company, so changing the
 *    order warehouse naturally fetches fresh figures;
 *  - when the feature is disabled for a company we stop calling the server
 *    for that company for DISABLED_TTL.
 */
const CACHE_TTL = 30000;
const DISABLED_TTL = 60000;

const cache = new Map();
const disabledUntil = new Map();

export function isStockPopupDisabled(companyId) {
    const until = disabledUntil.get(companyId || 0);
    return Boolean(until && until > Date.now());
}

export function clearStockPopupCache() {
    cache.clear();
    disabledUntil.clear();
}

export function fetchStockPopupData(orm, params) {
    const { productId, warehouseId, companyId, orderId } = params;
    const key = [productId, warehouseId || 0, companyId || 0].join("|");
    const hit = cache.get(key);
    if (hit && Date.now() - hit.ts < CACHE_TTL) {
        return hit.promise;
    }
    const caller = orm.silent || orm; // no loading indicator for hovers
    const promise = caller
        .call("product.product", "get_sale_line_stock_popup_data", [productId], {
            warehouse_id: warehouseId || false,
            company_id: companyId || false,
            order_id: orderId || false,
        })
        .then(
            (result) => {
                if (!result || !result.enabled) {
                    disabledUntil.set(companyId || 0, Date.now() + DISABLED_TTL);
                }
                return result;
            },
            (error) => {
                cache.delete(key);
                throw error;
            }
        );
    cache.set(key, { ts: Date.now(), promise });
    return promise;
}
