# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': "Custom Partner",
    'summary': """ Résumé du module""",
    'description' : "RESUME DU MODULE QUI N'apparais que sur l'installation de odoo",
    'version': '16.0.1.0',
    'category': 'Sales/CRM',
#
    'company': 'Elosys',
    'author' : 'Elosys',
    'maintainer': 'Elosys',
    # 'support' : "ADRESSE MAIL POUR LES RECLAMATIONS",
    'website' : "http://www.elosys.net/",
    'contributors' : [
        "1 <Chems Eddine SAHININE>",
        
    ],
#
    "license": "LGPL-3",
    "price": 0.0,
    "currency": 'EUR',
    # 'live_test_url' : "LIEN VERS FORMULAIRE POUR CREATION DE BASES TEST PROPRE A LA VERSION DU MODULE",
    'images' : ['images/banner.png'],
#
    'depends' : [
            'base',
            'account',
    ],
#
    'data': [
        'views/res_partner.xml',
    ],
#    
#    'demo' : [
#        "DONNEES DE DEMONSTRATION"
#    ],
#    
#    'external_dependencies' : 'DEPENDANCES EXTERNES',
#    
    # 'sequence': 1,
    'installable': True,
    'auto_install': False,
    "application": False,
}
