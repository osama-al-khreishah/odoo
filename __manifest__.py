{
    'name': 'Real Estate Management',
    'version': '1.0',
    'summary': 'Manage real estate properties',
    'description': 'A module to manage real estate properties.',
    'author': 'Osama alkhreishah',
    'website': 'www.linkedin.com/in/osama-khreishah-980559255',
    'category': 'Real Estate',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
	      'views/estate_property_views.xml',
        'views/users_views.xml',
	      'views/estate_menus.xml'
      ],

    'installable': True,
    'application': True,  
}
