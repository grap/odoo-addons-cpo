# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, api, fields


class ComputedPurchaseOrderLine(models.Model):
    _inherit = 'computed.purchase.order.line'

    # @api.onchange('product_id')
    # def onchange_product_id(self):
    #     super(ComputedPurchaseOrderLine, self).onchange_product_id()
    #     self.average_consumption = self.product_id.average_consumption_pvi
    pvi_draft_qty = fields.Float(
        'PVI Draft Outgoing Quantity', compute='_pvi_qty_available',
        help="Draft sales", store=False)
    pvi_qty = fields.Float(
        'PVI Outgoing Quantity', compute='_pvi_qty_available',
        help="Draft sales", store=False)

    @api.multi
    def _pvi_qty_available(self):
        for cpol in self:
            if cpol.product_id.id:
                pvi = [True]
                parametres = ['draft']
                if cpol.computed_purchase_order_id.compute_pvi_d_quantity:
                    cpol.pvi_draft_qty = cpol.product_id.\
                        custom_average_consumption(parametres, pvi)[0]
                if cpol.computed_purchase_order_id.compute_pvi_quantity:
                    parametres = ['pvi_confirmed']
                    cpol.pvi_qty = cpol.product_id.\
                        custom_average_consumption(parametres, pvi)[0]

    @api.multi
    def _get_computed_qty(self):
        for cpol in self:
            computed_qty = 0
            computed_qty = cpol.qty_available
            if cpol.computed_purchase_order_id.compute_pending_quantity:
                computed_qty += (cpol.incoming_qty - cpol.outgoing_qty)
            if cpol.computed_purchase_order_id.compute_draft_quantity:
                computed_qty += (cpol.draft_incoming_qty -
                                 cpol.draft_outgoing_qty)
            if cpol.computed_purchase_order_id.compute_pvi_d_quantity:
                computed_qty -= cpol.pvi_draft_qty
            if cpol.computed_purchase_order_id.compute_pvi_quantity:
                computed_qty -= cpol.pvi_qty
            cpol.computed_qty = computed_qty
