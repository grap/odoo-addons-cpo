# -*- encoding: utf-8 -*-
##############################################################################
#
#    Purchase - Computed Purchase Order Glue Module for Sale for Odoo
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

{
    'name': 'Computed Purchase Order - Sale',
    'version': '11.0.1.0.0',
    'category': 'Purchase',
    'description': """
Glue module that allow to include draft sale_orders in the
purchase_compute_order calculation.
==========================================================
===================================

Contacts :
----------
    * Julien WESTE;
    * Sylvain LE GAL (https://twitter.com/legalsylvain);
    * <informatique@grap.coop> for any help or question about this module.
    """,
    'author': 'GRAP',
    'website': 'http://www.grap.coop',
    'license': 'AGPL-3',
    'depends': [
        'purchase_compute_order',
        'sale',
    ],
    'auto_install': True,
}
