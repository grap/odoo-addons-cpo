# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# © 2018 FactorLibre - Álvaro Marcos <alvaro.marcos@factorlibre.com>
from openerp import models, fields, api


class ComputedPurchaseOrder(models.Model):
    _inherit = 'computed.purchase.order'

    compute_pvi_quantity = fields.Boolean('PVI quantity taken in account',
                                          default=True)

    compute_pvi_d_quantity = fields.Boolean('Draft PVI taken in account',
                                            default=True)

    @api.multi
    def write_active_product_stock(self, cpo, cpol_list):
        product_env = self.env['product.product']
        parametres = []
        pvi = []
        if cpo.compute_pending_quantity:
            parametres.append('sale')
            parametres.append('done')
            pvi.append(False)
        if cpo.compute_draft_quantity:
            parametres.append('draft')
            pvi.append(False)
        if cpo.compute_pvi_d_quantity:
            parametres.append('draft')
            pvi.append(True)
        if cpo.compute_pvi_quantity:
            parametres.append('pvi_confirmed')
            pvi.append(True)
        for cpol in cpol_list:
            product_id = product_env.browse(int(cpol[2]['product_id']))
            cpol[2].update({
                'average_consumption': product_id.\
                    custom_average_consumption(parametres, pvi)[1] or 0.0
            })
        super(ComputedPurchaseOrder,
              self).write_active_product_stock(cpo, cpol_list)

    # @api.onchange('compute_pvi_d_quantity')
    # @api.multi
    # def active_draft(self):
    #     self.ensure_one()
    #     if self.compute_pvi_d_quantity and not self.compute_draft_quantity:
    #         self.compute_draft_quantity = True
