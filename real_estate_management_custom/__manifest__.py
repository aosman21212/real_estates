{
    'name': 'Real Estate Management',
    'version': '19.0.1.0.0',
    'summary': 'Manage buildings, units, leases, maintenance and utility charges',
    'description': """
        Real Estate Management module for Odoo 19.
        Features:
        - Building and unit management
        - Lease contract management with automatic recurring invoices
        - Maintenance request tracking with vendor bills
        - Utility charge billing per lease period
    """,
    'category': 'Real Estate',
    'author': 'leapai.ai',
    'website': 'https://leapai.ai/en/',
    'support': 'abdzoro89@gmail.com',
    'maintainer': 'a.osman@bab.com.sa',
    'depends': ['base', 'account', 'mail'],
    'images': [
        'static/description/banner.png',
        'static/description/thumbnail.png',
    ],
    'data': [
        'security/real_estate_security.xml',
        'security/ir.model.access.csv',
        'data/real_estate_sequence.xml',
        'data/real_estate_cron.xml',
        'views/real_estate_building_views.xml',
        'views/real_estate_unit_views.xml',
        'views/real_estate_lease_views.xml',
        'views/real_estate_maintenance_views.xml',
        'views/real_estate_menus.xml',
    ],
    'demo': [
        'demo/real_estate_demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
