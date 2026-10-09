# -*- coding: utf-8 -*-
# =============================================================================
#  Real Estate Management
# -----------------------------------------------------------------------------
#  Location  : King Abdulaziz Branch Road, Riyadh, Saudi Arabia
#  Email     : sales@leapai.ai
#  Phone     : +966 53 553 3627
#  Website   : https://leapai.ai
#  Developer : Abdulkaraim Osman — Tech Manager | Backend Engineer | DevOps Engineer
#              at Bab International Corp For Specialized Services
#  LinkedIn  : https://www.linkedin.com/in/abdulkaraim-o-385b7a110/
# =============================================================================
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
    'maintainer': 'Abdulkaraim Osman',
    'support': 'sales@leapai.ai',
    'website': 'https://leapai.ai/en/',
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
