# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Glue Module for Point Of Sale for Odoo
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

from openerp import models, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # Private section
    @api.multi
    def _get_draft_outgoing_qty(self):
        super(ProductProduct, self)._get_draft_outgoing_qty()
        pol_obj = self.env['pos.order.line']
        pol_ids = pol_obj.search([
            ('state', '=', 'draft'),
            ('product_id', 'in', map(lambda p: p.id, self))
        ])
        draft_qty = {}

        for line in pol_ids:
            draft_qty.setdefault(line.product_id.id, 0)
            draft_qty[line.product_id.id] -= line.qty
        for pp in self:
            pp.draft_outgoing_qty += draft_qty.get(pp.id, 0)
