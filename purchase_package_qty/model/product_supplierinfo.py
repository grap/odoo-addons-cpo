# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Package Quantity Module for Odoo
#    Copyright (C) 2013-Today GRAP (http://www.grap.coop)
#    @author Julien WESTE
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#    Copyright (C) 2015 FactorLibre
#    @author Hugo Santos <hugo.santos@factorlibre.com>
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
import openerp.addons.decimal_precision as dp


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    package_qty = fields.Float(
        'Package Qty', required=True,
        digits_compute=dp.get_precision('Product UoM'),
        help="""The quantity of products in the supplier package."""
        """ You will always have to buy a multiple of this quantity.""",
        default=1)
    indicative_package = fields.Boolean(
        'Indicative Package',
        help="""If checked, the system will not force you to purchase """
        """a strict multiple of package quantity""",
        default=False)

    # Constraints section
    @api.multi
    def _check_package_qty(self):
        for psi in self:
            if psi.package_qty == 0:
                return False
        return True

    _constraints = [
        (_check_package_qty, 'Error: The package quantity cannot be 0.',
            ['package_qty']),
    ]

    # Init section
    @api.model
    def _init_package_qty(self):
        for psi in self.sudo().search([]):
            package_qty = max(psi.min_qty, 1)
            psi.sudo().write({'package_qty': package_qty})
        return True
