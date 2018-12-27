from openerp import models, fields, api


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    @api.multi
    def _make_po_lines(self):
        self.ensure_one()
        all_lines = []
        for line in self.line_ids:
            if line.purchase_qty != 0:
                line_values = {
                    'name': line.product_id.display_name,
                    'product_qty': line.purchase_qty,
                    'date_planned': (
                        self.incoming_date or fields.Date.context_today(self)),
                    'product_uom': line.product_id.uom_po_id.id,
                    'product_id': line.product_id.id,
                    'price_unit': line.product_price_inv,
                    'taxes_id': [(
                        6, 0,
                        [x.id for x in line.product_id.supplier_taxes_id])],
                    'discount': line.discount,
                }
                all_lines.append((0, 0, line_values),)
        return all_lines
