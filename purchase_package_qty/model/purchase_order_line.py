# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Package Quantity Module for Odoo
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

from math import ceil

from openerp.osv.osv import except_osv
from openerp.osv.orm import Model
from openerp.tools.translate import _


class PurchaseOrderLine(Model):
    _inherit = 'purchase.order.line'

    # Constraints section
    # TODO: Rewrite me in _contraint, if the Orm V8 allows param in message.
    def _check_purchase_qty(self, cr, uid, ids, context=None):
        for pol in self.browse(cr, uid, ids, context=context):
            if pol.order_id.state not in ('draft', 'sent'):
                continue
            if not pol.product_id:
                return True
            supplier_id = pol.order_id.partner_id.id
            found = False
            for psi in pol.product_id.seller_ids:
                if psi.name.id == supplier_id:
                    package_qty = psi.package_qty
                    indicative = psi.indicative_package
                    found = True
                    break
            if not found:
                return True
            if not indicative:
                if (int(pol.product_qty / package_qty) !=
                        pol.product_qty / package_qty):
                    raise except_osv(
                        _("Package Error!"),
                        _(
                            """You have to buy a multiple of the package"""
                            """ qty or change the package settings in the"""
                            """ supplierinfo of the product for the"""
                            """ following line:"""
                            """ \n - Product: %s;"""
                            """ \n - Quantity: %s;"""
                            """ \n - Unit Price: %s;""" % (
                                pol.product_id.name, pol.product_qty,
                                pol.price_unit)))
        return True

    def create(self, cr, uid, vals, context=None):
        res = super(PurchaseOrderLine, self).create(
            cr, uid, vals, context=context)
        self._check_purchase_qty(cr, uid, [res], context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(PurchaseOrderLine, self).write(
            cr, uid, ids, vals, context=context)
        self._check_purchase_qty(cr, uid, ids, context=context)
        return res

    # Views section
    def onchange_product_id(
            self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False,
            date_planned=False, name=False, price_unit=False, context=None):
        res = super(PurchaseOrderLine, self).onchange_product_id(
            cr, uid, ids, pricelist_id, product_id, qty, uom_id, partner_id,
            date_order=date_order, fiscal_position_id=fiscal_position_id,
            date_planned=date_planned, name=name, price_unit=price_unit,
            context=context)
        if product_id:
            product_obj = self.pool.get('product.product')
            product = product_obj.browse(cr, uid, product_id, context=context)
            for supplier in product.seller_ids:
                if partner_id and (supplier.name.id == partner_id):
                    package_qty = supplier.package_qty
                    indicative = supplier.indicative_package
                    if (not(indicative) and
                            int(qty / package_qty) != qty / package_qty):
                        res['warning'] = {
                            'title': _('Warning!'),
                            'message': _(
                                """The selected supplier only sells"""
                                """this product by %s %s""") % (
                                supplier.package_qty,
                                supplier.product_uom.name)}
                        qty = ceil(qty / package_qty) * package_qty
                        res['value'].update({'product_qty': qty})
        return res
