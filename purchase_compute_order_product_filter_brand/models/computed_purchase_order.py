# -*- coding: utf-8 -*-
# © 2019 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    product_brand = fields.Many2one('product.brand', 'Product brand')

    @api.multi
    def _active_product_stock_product_domain(self, psi_ids):
        product_domain = super(ComputedPurchaseOrder, self).\
            _active_product_stock_product_domain(psi_ids)
        if self.product_brand:
            product_domain.append(
                ('product_brand_id', '=', self.product_brand.id))
        return product_domain
