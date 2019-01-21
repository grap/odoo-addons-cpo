# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    product_season = fields.Many2one('product.season', 'Product Season')

    @api.multi
    def _active_product_stock_product_domain(self, psi_ids):
        product_domain = super(ComputedPurchaseOrder, self).\
            _active_product_stock_product_domain(psi_ids)
        if self.product_season:
            product_domain.append(('season_id', '=', self.product_season.id))
        return product_domain
