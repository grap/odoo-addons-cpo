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

from openerp import models, api


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    # # Constraints section
    # _sql_constraints = [
    #     (
    #         'psi_product_name_uniq', 'unique(name, product_tmpl_id)',
    #         """You cannot register several times the same supplier on a"""
    #         """ product!"""),
    # ]
    # ALTER TABLE product_supplierinfo DROP CONSTRAINT
    # product_supplierinfo_psi_product_name_uniq;

    # Private section
    # @api.model
    # def _delete_duplicates(self):
    #     cr = self.env.cr
    #     query = """
    #         SELECT pp.id
    #         FROM
    #             product_supplierinfo psi
    #             INNER JOIN product_template pt ON psi.product_tmpl_id = pt.id
    #             INNER JOIN product_product pp ON pp.product_tmpl_id = pt.id
    #         GROUP BY
    #             pp.id, psi.name
    #         HAVING
    #             count(*) > 1"""
    #     cr.execute(query)
    #     product_ids = [x[0] for x in cr.fetchall()]
    #     products = self.env['product.product'].browse(product_ids)
    #
    #     deleted_ids = []
    #     for product in products:
    #         delete = False
    #         for psi in product.seller_ids:
    #             if delete:
    #                 deleted_ids.append(psi.id)
    #                 psi.unlink()
    #             else:
    #                 delete = True
    #     return deleted_ids
