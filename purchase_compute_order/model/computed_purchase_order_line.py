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
from openerp import models, fields, api, _, exceptions
import openerp.addons.decimal_precision as dp


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
    weight_net = fields.Float('Net Weight', related='product_id.weight_net',
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
        'Quantity On Hand', related='product_id.qty_available',
        help="The available quantity on hand for this product")
    incoming_qty = fields.Float(
        'Incoming Quantity', related='product_id.incoming_qty',
        help="Virtual incoming entries", store=True)
    outgoing_qty = fields.Float(
        'Outgoing Quantity', related='product_id.outgoing_qty',
        help="Virtual outgoing entries", store=True)
    draft_incoming_qty = fields.Float(
        'Draft Incoming Quantity', related='product_id.draft_incoming_qty',
        help="Draft purchases", store=True)
    draft_outgoing_qty = fields.Float(
        'Draft Outgoing Quantity', related='product_id.draft_outgoing_qty',
        help="Draft sales", store=True)
    computed_qty = fields.Float(
        string='Computed Stock', compute='_get_computed_qty',
        help="The sum of all quantities selected.",
        digits_compute=dp.get_precision('Product UoM'))

    # Constraints section
    _sql_constraints = [
        (
            'product_id_uniq', 'unique(computed_purchase_order_id,product_id)',
            'Product must be unique by computed purchase order!'),
    ]

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
        psi_obj = self.env['product.supplierinfo']

        for cpol in self:
            unit_price = cpol.product_price
            cpo_product_price = cpol.computed_purchase_order_id.product_price
            cpo_partner_id = cpol.computed_purchase_order_id.partner_id.id

            if pricelist:
                product_tmpl = cpol.product_id.product_tmpl_id
                psi = psi_obj.search([
                    ('name', '=', cpo_partner_id),
                    ('product_tmpl_id', '=', product_tmpl.id)
                ])
                if psi:
                    unit_price = (
                        psi.pricelist_ids and
                        psi.pricelist_ids[0].price or
                        psi.product_tmpl_id.standard_price)

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
        psi_obj = self.env['product.supplierinfo']
        for cpol in self:
            if not cpol.product_id:
                cpol.product_code_inv = None
                cpol.product_name_inv = None
                cpol.product_price_inv = 0.0
                cpol.package_quantity_inv = 0.0
            elif cpol.state in ('updated', 'new'):
                cpol.product_code_inv = cpol.product_code
                cpol.product_name_inv = cpol.product_name
                cpol.product_price_inv = cpol._product_price_based_on(),
                cpol.package_quantity_inv = cpol.package_quantity
            else:
                psi = psi_obj.search([
                    ('name', '=',
                        cpol.computed_purchase_order_id.partner_id.id),
                    ('product_tmpl_id', '=',
                        cpol.product_id.product_tmpl_id.id)
                ])
                if psi:
                    cpol.product_code_inv = psi.product_code
                    cpol.product_name_inv = psi.product_name
                    cpol.product_price_inv = cpol._product_price_based_on(True)
                    cpol.package_quantity_inv = psi.package_qty

    @api.multi
    def _set_product_code(self, field_value):
        vals = {'product_code': field_value}
        if self.state == 'up_to_date':
            vals.update({'state': 'updated'})
        return self.write(vals)

    @api.multi
    def _set_product_name(self, field_value):
        vals = {'product_name': field_value}
        if self.state == 'up_to_date':
            vals.update({'state': 'updated'})
        return self.write(vals)

    @api.multi
    def _set_product_price(self, field_value):
        vals = {'product_price': field_value}
        if self.state == 'up_to_date':
            vals.update({'state': 'updated'})
        return self.write(vals)

    @api.multi
    def _set_package_quantity(self, field_value):
        vals = {'package_quantity': field_value}
        if self.state == 'up_to_date':
            vals.update({'state': 'updated'})
        return self.write(vals)

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
            psi_obj = self.env['product.supplierinfo']
            pp = self.product_id
            computed_qty = pp.qty_available

            cpo = self.computed_purchase_order_id
            if cpo:
                # Check if the product is already in the list.
                products = [x.product_id.id for x in cpo.line_ids]
                if pp.id in products:
                    raise exceptions.Warning(
                        _('This product is already in the list!'))

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
            self.weight_net = pp.weight_net
            self.uom_po_id = pp.uom_id.id
            self.product_price_inv = 0
            self.package_quantity_inv = 0
            self.average_consumption = pp.average_consumption

            # If product is in the supplierinfo,
            # retrieve values and set state up_to_date
            if cpo.partner_id:
                psi = psi_obj.search([
                    ('name', '=', cpo.partner_id.id),
                    ('product_tmpl_id', '=', pp.product_tmpl_id.id)
                ])
                if psi:
                    self.product_code_inv = psi.product_code
                    self.product_name_inv = psi.product_name
                    self.product_price_inv = (
                        psi.pricelist_ids and psi.pricelist_ids[0].price or 0)
                    self.package_quantity_inv = psi.package_qty
                    self.uom_po_id = psi.product_uom.id
                    self.state = 'up_to_date'

    @api.multi
    def unlink_psi(self):
        psi_obj = self.env["product.supplierinfo"]
        psi2unlink = []
        for cpol in self:
            cpo = cpol.computed_purchase_order_id
            partner_id = cpo.partner_id.id
            product_tmpl_id = cpol.product_id.product_tmpl_id.id
            psi_ids = psi_obj.search([
                ('name', '=', partner_id),
                ('product_tmpl_id', '=', product_tmpl_id)
            ])
            psi2unlink += psi_ids
        for psi in psi2unlink:
            psi.unlink()
        self.unlink()
        return True

    @api.multi
    def create_psi(self):
        psi_obj = self.env['product.supplierinfo']
        for cpol in self:
            cpo = cpol.computed_purchase_order_id
            partner_id = cpo.partner_id.id
            product_tmpl_id = cpol.product_id.product_tmpl_id.id

            values = {
                'name': partner_id,
                'product_name': cpol.product_name,
                'product_code': cpol.product_code,
                'product_uom': cpol.uom_po_id.id,
                'package_qty': cpol.package_quantity_inv,
                'min_qty': cpol.package_quantity,
                'product_tmpl_id': product_tmpl_id,
                'pricelist_ids': [(0, 0, {
                    'min_quantity': 0, 'price': cpol.product_price_inv})],
            }
            psi_id = psi_obj.create(values)
            cpol.write({'state': 'up_to_date'})
            return psi_id
