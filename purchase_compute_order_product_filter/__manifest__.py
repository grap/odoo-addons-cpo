# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Computed Purchase Order: Product Filters',
    'version': '11.0.1.0.0',
    'category': 'Purchase',
    'depends': [
        'purchase_compute_order',
    ],
    'author': 'Odoo Community Association (OCA),FactorLibre',
    'license': 'AGPL-3',
    'website': 'http://www.factorlibre.com',
    'data': [
        'security/ir.model.access.csv',
        'data/product_state_info_data.xml',
        'views/compute_order_view.xml'
    ],
    'installable': True,
    'application': False
}
