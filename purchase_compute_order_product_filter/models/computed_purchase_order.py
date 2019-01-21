# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class ProductStateInfo(models.Model):
    _name = 'product.state.info'

    name = fields.Char('State', readonly=True, required=True, translate=True)
    code = fields.Char('State Code', readonly=True, required=True)


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    filter_by_product_category = fields.Boolean('Filter by product Category')
    product_category_ids = fields.Many2many(
        'product.category', string='Product Category')
    filter_by_product_state = fields.Boolean('Filter by product state')
    product_state_ids = fields.Many2many(
        'product.state.info', string='Product State')

    @api.multi
    def _active_product_stock_product_domain(self, psi_ids):
        self.ensure_one()
        product_domain = super(ComputedPurchaseOrder, self).\
            _active_product_stock_product_domain(psi_ids)
        product_domain.append(('type', '!=', 'pack'))
        if self.product_state_ids and self.filter_by_product_state:
            if ('state', 'not in', ('end', 'obsolete')) in product_domain:
                product_domain.remove(('state', 'not in', ('end', 'obsolete')))
            states = []
            for state in self.product_state_ids:
                states.append(state.code)
            product_domain.append(('state', 'in', states))
        if self.product_category_ids and self.filter_by_product_category:
            categ_ids = self.product_category_ids.ids
            product_domain += [
                '|', ('categ_id', 'in', categ_ids),
                ('categ_ids', 'in', categ_ids)
            ]
        return product_domain
