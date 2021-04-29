# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    principal_supplier = fields.Many2one('product.supplierinfo',
                                         'Principal Supplier',
                                         compute='_calc_principal_supplier')

    @api.multi
    def _calc_principal_supplier(self):
        for prod in self:
            prod.principal_supplier = self.env['product.supplierinfo'].search([
                ('id', 'in', prod.seller_ids.ids)], order="sequence", limit=1)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    draft_incoming_qty = fields.Float(
        compute='_get_draft_incoming_qty', string='Draft Incoming')
    draft_outgoing_qty = fields.Float(
        compute='_get_draft_outgoing_qty', string='Draft Outgoing')

    @api.multi
    def _get_draft_incoming_qty(self):
        """ Compute incoming qty of products in draft purchase order.
            You can overload this function, in glue module.
        """
        product_ids = [p.id for p in self]
        pol_model = self.env['purchase.order.line']
        pol_ids = pol_model.search(
            self._get_draft_incoming_qty_domain(product_ids))
        draft_qty = {}

        for pol in pol_ids:
            draft_qty.setdefault(pol.product_id.id, 0)
            draft_qty[pol.product_id.id] +=\
                pol.product_qty / pol.product_uom.factor\
                * pol.product_id.uom_id.factor

        for product in self:
            product.draft_incoming_qty = draft_qty.get(product.id, 0)

    @api.multi
    def _get_draft_incoming_qty_domain(self, product_ids):
        return [
            ('state', '=', 'draft'),
            ('product_id', 'in', product_ids)
        ]

    @api.multi
    def _get_draft_outgoing_qty(self):
        """ empty function.
            Please Overload this function, in glue module.
        """
        for product in self:
            product.draft_outgoing_qty = 0
