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

from openerp.osv.orm import Model


class product_product(Model):
    _inherit = 'product.product'

    # Private section
    def _get_draft_outgoing_qty(
            self, cr, uid, ids, fields, arg, context=None):
        """ empty function.
            Please Overload this function, in glue module.
        """
        res = super(product_product, self)._get_draft_outgoing_qty(
            cr, uid, ids, fields, arg, context=context)
        pol_obj = self.pool.get('pos.order.line')
        pol_ids = pol_obj.search(cr, uid, [
            ('state', '=', 'draft'),
            ('product_id', 'in', ids)], context=context)
        draft_qty = {}

        for line in pol_obj.browse(cr, uid, pol_ids, context=context):
            draft_qty.setdefault(line.product_id.id, 0)
            draft_qty[line.product_id.id] -= line.qty
        for pp in self.browse(cr, uid, ids, context=context):
            res.setdefault(pp.id, 0)
            res[pp.id] += draft_qty.get(pp.id, 0)
        return res
