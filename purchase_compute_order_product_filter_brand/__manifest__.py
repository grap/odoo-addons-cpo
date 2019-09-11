# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Computed Purchase Order: Product Filters Brand',
    'version': '11.0.1.0.0',
    'category': 'Purchase',
    'depends': [
        'product_brand',
        'purchase_compute_order',
        'purchase_compute_order_product_filter',
    ],
    'author': 'Odoo Community Association (OCA),FactorLibre',
    'license': 'AGPL-3',
    'website': 'http://www.factorlibre.com',
    'data': [
        'views/compute_order_view.xml'
    ],
    'installable': True,
    'application': False
}
