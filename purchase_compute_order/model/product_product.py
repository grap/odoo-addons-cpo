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

from openerp.osv import fields
from openerp.osv.orm import Model


class product_product(Model):
    _inherit = 'product.product'

    # Field Function section
    def _get_draft_incoming_qty_column(
            self, cr, uid, ids, fields, arg, context=None):
        return self._get_draft_incoming_qty(
            cr, uid, ids, fields, arg, context=context)

    def _get_draft_outgoing_qty_column(
            self, cr, uid, ids, fields, arg, context=None):
        return self._get_draft_outgoing_qty(
            cr, uid, ids, fields, arg, context=context)

    _columns = {
        'draft_incoming_qty': fields.function(
            _get_draft_incoming_qty_column, type='float',
            string='Draft Incoming'),
        'draft_outgoing_qty': fields.function(
            _get_draft_outgoing_qty_column, type='float',
            string='Draft Outgoing'),
    }

    # Private section
    def _get_draft_incoming_qty(self, cr, uid, ids, fields, arg, context=None):
        """ Compute incoming qty of products in draft purchase order.
            You can overload this function, in glue module.
        """
        res = {}
        pol_obj = self.pool.get('purchase.order.line')
        pol_ids = pol_obj.search(
            cr, uid, [('state', '=', 'draft'), ('product_id', 'in', ids)],
            context=context)
        draft_qty = {}

        for pol in pol_obj.browse(cr, uid, pol_ids, context=context):
            draft_qty.setdefault(pol.product_id.id, 0)
            draft_qty[pol.product_id.id] +=\
                pol.product_qty / pol.product_uom.factor\
                * pol.product_id.uom_id.factor

        for pp in self.browse(cr, uid, ids, context=context):
            res[pp.id] = draft_qty.get(pp.id, 0)
        return res

    def _get_draft_outgoing_qty(self, cr, uid, ids, fields, arg, context=None):
        """ empty function.
            Please Overload this function, in glue module.
        """
        res = {}
        for pp in self.browse(cr, uid, ids, context=context):
            res[pp.id] = 0
        return res
