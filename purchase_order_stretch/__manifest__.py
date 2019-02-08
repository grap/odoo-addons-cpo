{
    'name': 'Purchase Order Stretch',
    'version': '11.0.1.0.0',
    'category': 'Purchase',
    'author': 'FactorLibre',
    'license': 'AGPL-3',
    'depends': [
        'purchase',
        'product',
        'purchase_compute_order',
        'purchase_compute_order_discount',
    ],
    'data': [
        "views/purchase_order.xml",
    ],
}
