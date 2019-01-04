from openerp import models, api


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    @api.multi
    def write_line_values(self, line):
        values = super(ComputedPurchaseOrder, self).write_line_values(line)
        values['discount'] = line.discount
        return values
