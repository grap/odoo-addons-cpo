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
import logging
from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class ComputedPurchaseOrderLine(models.Model):
    _description = 'Computed Purchase Order Line'
    _name = 'computed.purchase.order.line'
    _order = 'sequence'

    @api.model
    def _get_state_selection(self):
        return [
            ('new', 'New'),
            ('up_to_date', 'Up to date'),
            ('updated', 'Updated'),
        ]

    # Columns section
    computed_purchase_order_id = fields.Many2one(
        'computed.purchase.order', 'Order Reference', required=True,
        ondelete='cascade')
    state = fields.Selection(
        '_get_state_selection', 'State', required=True, readonly=True,
        help="Shows if the product's information has been updated",
        default='new')
    sequence = fields.Integer(
        'Sequence',
        help="""Gives the sequence order when displaying a list of"""
        """ purchase order lines.""")
    product_id = fields.Many2one(
        'product.product', string='Product', required=True)
    uom_id = fields.Many2one('product.uom', string="UoM",
                             related='product_id.uom_id', readonly='True')
    product_code = fields.Char('Supplier Product Code')
    product_code_inv = fields.Char(
        'Supplier Product Code',
        compute='_get_product_information', inverse='_set_product_code',
        help="""This supplier's product code will be used when printing"""
        """ a request for quotation. Keep empty to use the internal"""
        """ one.""")
    product_name = fields.Char('Supplier Product Name')
    product_name_inv = fields.Char(
        'Supplier Product Name',
        compute='_get_product_information', inverse='_set_product_name',
        help="""This supplier's product name will be used when printing"""
        """ a request for quotation. Keep empty to use the internal"""
        """ one.""")
    product_price = fields.Float(
        'Supplier Product Price',
        digits_compute=dp.get_precision('Product Price'))
    product_price_inv = fields.Float(
        'Supplier Product Price',
        compute='_get_product_information', inverse='_set_product_price')
    package_quantity = fields.Float('Package quantity')
    package_quantity_inv = fields.Float(
        'Package quantity', compute='_get_product_information',
        inverse='_set_package_quantity')
    weight_net = fields.Float('Net Weight', related='product_id.weight',
                              readonly='True')
    uom_po_id = fields.Many2one('product.uom', 'UoM', required=True)
    average_consumption = fields.Float('Average Consumption', digits=(12, 3))
    stock_duration = fields.Float(
        'Stock Duration (Days)',
        compute='_compute_stock_duration', readonly='True',
        help="Number of days the stock should last.")
    purchase_qty = fields.Float(
        'Quantity to purchase', required=True,
        help="The quantity you should purchase.", default=0)
    manual_input_output_qty = fields.Float(
        string='Manual variation',
        help="""Write here some extra quantity depending of some"""
        """ input or output of products not entered in the software\n"""
        """- negative quantity : extra output ; \n"""
        """- positive quantity : extra input.""", default=0)
    qty_available = fields.Float(
        'Quantity On Hand', compute='_product_qty_available',
        help="The available quantity on hand for this product")
    incoming_qty = fields.Float(
        'Incoming Quantity', compute='_product_qty_available',
        help="Virtual incoming entries", store=False)
    outgoing_qty = fields.Float(
        'Outgoing Quantity', compute='_product_qty_available',
        help="Virtual outgoing entries", store=False)
    draft_incoming_qty = fields.Float(
        'Draft Incoming Quantity', compute='_product_qty_available',
        help="Draft purchases", store=False)
    draft_outgoing_qty = fields.Float(
        'Draft Outgoing Quantity', compute='_product_qty_available',
        help="Draft sales", store=False)
    computed_qty = fields.Float(
        string='Computed Stock', compute='_get_computed_qty',
        help="The sum of all quantities selected.",
        digits_compute=dp.get_precision('Product UoM'))
    supplier = fields.Many2one('product.supplierinfo', 'Supplier')
    temp_value = fields.Float("Temporal value")

    # Constraints section
    _sql_constraints = [
        (
            'product_id_uniq', 'unique(computed_purchase_order_id,product_id)',
            'Product must be unique by computed purchase order!'),
    ]

    @api.multi
    def _line_product_supplier_info(self):
        self.ensure_one()
        cpo_partner_id = self.computed_purchase_order_id.partner_id.id
        product_tmpl_id = self.product_id.product_tmpl_id.id
        psi = self.env['product.supplierinfo'].search([
            ('name', '=', cpo_partner_id),
            ('product_tmpl_id', '=', product_tmpl_id),
        ], order='sequence', limit=1)
        return psi

    @api.multi
    def _product_qty_available(self):
        for cpol in self:
            if cpol.product_id.id:
                product_qty = cpol.product_id._product_available()[
                    cpol.product_id.id]
                cpol.qty_available = product_qty['qty_available']
                cpol.outgoing_qty = product_qty['outgoing_qty']
                cpol.incoming_qty = product_qty['incoming_qty']
                cpol.draft_incoming_qty = cpol.product_id.draft_incoming_qty
                cpol.draft_outgoing_qty = cpol.product_id.draft_outgoing_qty

    @api.multi
    def _get_computed_qty(self):
        for cpol in self:
            computed_qty = cpol.qty_available
            if cpol.computed_purchase_order_id.compute_pending_quantity:
                computed_qty += (cpol.incoming_qty - cpol.outgoing_qty)
            if cpol.computed_purchase_order_id.compute_draft_quantity:
                computed_qty += (cpol.draft_incoming_qty -
                                 cpol.draft_outgoing_qty)
            cpol.computed_qty = computed_qty

    @api.multi
    def _product_price_based_on(self, pricelist=False):
        pool_purchase_line = self.env['purchase.order.line']

        for cpol in self:
            unit_price = cpol.product_price
            cpo_product_price = cpol.computed_purchase_order_id.product_price
            cpo_partner_id = cpol.computed_purchase_order_id.partner_id.id
            if pricelist:
                psi = cpol._line_product_supplier_info()
                if psi:
                    # TODO: Check field pricelist_ids on psi
                    # unit_price = (
                    #     psi.pricelist_ids and
                    #     psi.pricelist_ids[0].price or
                    # #     psi.product_tmpl_id.standard_price)
                    # if psi.price and purchase_qty >= psi.min_qty:
                    #     unit_price = psi.price
                    # else:
                    # if psi.price and cpol.purchase_qty >= psi.min_qty:
                    unit_price =\
                        psi.price or psi.product_tmpl_id.standard_price
                    # else:
                    #     unit_price = psi.product_tmpl_id.standard_price
            if cpo_product_price == 'last_purchase':
                purch_line_price = pool_purchase_line.search([
                    ('product_id', '=', cpol.product_id.id)
                ], limit=1, order='date_planned desc')
                if purch_line_price:
                    unit_price = purch_line_price.price_unit

            if cpo_product_price == 'last_purchase_supplier':
                purch_line_price = pool_purchase_line.search([
                    ('product_id', '=', cpol.product_id.id),
                    ('partner_id', '=', cpo_partner_id)
                ], limit=1, order='date_planned desc')
                if purch_line_price:
                    unit_price = purch_line_price.price_unit
        return unit_price

    @api.multi
    def _get_product_information(self):
        for cpol in self:
            if not cpol.product_id:
                cpol.product_code_inv = None
                cpol.product_name_inv = None
                cpol.product_price_inv = 0.0
                cpol.package_quantity_inv = 0.0
            elif cpol.state in ('updated', 'new'):
                cpol.product_code_inv = cpol.product_code
                cpol.product_name_inv = cpol.product_name
                cpol.product_price_inv = cpol._product_price_based_on()
                cpol.package_quantity_inv = cpol.package_quantity
            else:
                psi = cpol._line_product_supplier_info()
                if psi:
                    cpol.product_code_inv = psi.product_code
                    cpol.product_name_inv = psi.product_name
                    cpol.product_price_inv = cpol._product_price_based_on(True)
                    cpol.supplier = psi
                    cpol.package_quantity_inv = (
                        hasattr(psi,
                                'qty_multiple') and psi.qty_multiple or 1.0)

    @api.multi
    def _set_product_code(self):
        for line in self:
            if line.state == 'up_to_date':
                line.state = 'updated'
            line.product_code = line.product_code_inv

    @api.multi
    def _set_product_name(self):
        for line in self:
            if line.state == 'up_to_date':
                line.state = 'updated'
            line.product_name = line.product_name_inv

    @api.multi
    def _set_product_price(self):
        for line in self:
            if line.state == 'up_to_date':
                line.state = 'updated'
            line.product_price = line.product_price_inv

    @api.multi
    def _set_package_quantity(self):
        for line in self:
            if line.state == 'up_to_date':
                line.state = 'updated'
            line.package_quantity = line.package_quantity_inv

    @api.multi
    def _compute_stock_duration(self):
        for cpol in self:
            if not cpol.product_id:
                cpol.stock_duration = False
            else:
                if cpol.average_consumption == 0:
                    cpol.stock_duration = False
                else:
                    cpol.stock_duration = (
                        cpol.computed_qty + cpol.manual_input_output_qty)\
                        / cpol.average_consumption

    @api.multi
    def _store_stock_duration(self):
        return self._compute_stock_duration()

    # View Section
    @api.onchange('product_code_inv', 'product_name_inv', 'product_price_inv',
                  'package_quantity_inv')
    def onchange_product_info(self):
        self.state = 'updated'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        else:
            pp = self.product_id
            computed_qty = pp.qty_available

            cpo = self.computed_purchase_order_id
            if cpo:
                # Check if the product is already in the list.
                # products = [x.product_id.id for x in cpo.line_ids]
                # if products:
                #     raise exceptions.Warning(
                #         _('This product is already in the list!'))

                if cpo.compute_pending_quantity:
                    computed_qty += pp.incoming_qty + pp.outgoing_qty
                if cpo.compute_draft_quantity:
                    computed_qty += pp.draft_incoming_qty\
                        + pp.draft_outgoing_qty

            self.qty_available = pp.qty_available
            self.incoming_qty = pp.incoming_qty
            self.outgoing_qty = pp.outgoing_qty
            self.draft_incoming_qty = pp.draft_incoming_qty
            self.draft_outgoing_qty = pp.draft_outgoing_qty
            self.computed_qty = computed_qty
            # self.weight_net = pp.weight_net
            self.uom_po_id = pp.uom_id.id
            self.product_price_inv = 0
            self.package_quantity_inv = 0
            self.average_consumption = pp.average_consumption

            # If product is in the supplierinfo,
            # retrieve values and set state up_to_date
            if cpo.partner_id:
                psi = self._line_product_supplier_info()
                if psi:
                    self.product_code_inv = psi.product_code
                    self.product_name_inv = psi.product_name
                    # TODO: Check field pricelist_ids on psi
                    # self.product_price_inv = (
                    #     psi.pricelist_ids and
                    #     psi.pricelist_ids[0].price or 0)
                    self.product_price_inv = 0
                    self.package_quantity_inv =\
                        (hasattr(psi, 'qty_multiple') and psi.qty_multiple)
                    self.uom_po_id = psi.product_uom.id
                    self.state = 'up_to_date'

    @api.multi
    def unlink_psi(self):
        psi2unlink = []
        for cpol in self:
            psi_ids = cpol._line_product_supplier_info()
            psi2unlink += psi_ids
        for psi in psi2unlink:
            psi.unlink()
        self.unlink()
        return True

    @api.multi
    def _prepare_psi_values(self):
        self.ensure_one()
        cpo = self.computed_purchase_order_id
        partner_id = cpo.partner_id.id
        product_tmpl_id = self.product_id.product_tmpl_id.id
        values = {
            'name': partner_id,
            'product_name': self.product_name,
            'product_code': self.product_code,
            'product_uom': self.uom_po_id.id,
            'package_qty': self.package_quantity_inv,
            'min_qty': self.package_quantity,
            'product_tmpl_id': product_tmpl_id,
            'pricelist_ids': [(0, 0, {
                'min_quantity': 0, 'price': self.product_price_inv})],
        }
        return values

    @api.multi
    def create_psi(self):
        psi_obj = self.env['product.supplierinfo']
        for cpol in self:
            values = cpol._prepare_psi_values()
            psi_id = psi_obj.create(values)
            cpol.write({'state': 'up_to_date'})
            return psi_id
