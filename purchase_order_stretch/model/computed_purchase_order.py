# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, api


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    @api.multi
    def write_line_values(self, line):
        values = super(ComputedPurchaseOrder, self).write_line_values(line)
        values['supplier_id'] = line.supplier.id
        values['name'] = line.product_name
        return values
