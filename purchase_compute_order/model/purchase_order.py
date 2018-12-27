from openerp import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    computed_order = fields.Many2one('computed.purchase.order',
                                     'Computed Purchase Order')
