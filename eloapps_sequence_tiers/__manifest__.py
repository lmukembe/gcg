# -*- coding: utf-8 -*-
{
    'name': "Auto Référencement Des Tiers",
    "summary": "Générer automatiquement un numéro propre aux clients et aux fournisseurs.",
    "description": "Génére automatiquement un numéro propre aux clients et aux fournisseurs.",
    'category': 'Sales/CRM',
    "contributors": [
        "1 <Chems Eddine SAHININE>",
        
],
    'sequence': 1,
    'version': '16.0.1.0',
    "license": "LGPL-3",
    'author': 'Elosys',
    'website': "https://elosys.net",
    "price": 0.0,
    "currency": 'EUR',
    'live_test_url': "https://www.elosys.net/shop/auto-referencement-des-tiers-31?category=11#attr=58",

    'depends': [
        'base',
        'account',
        'eloapps_custom_partner',
    ],
    'data': [
        'data/accounting_group.xml',
        'data/sequences.xml',
        'views/res_partner.xml',
    ],
    
    'images': ['static/description/banner.gif'],
        
    'installable': True,
    'auto_install': False,
    'application': False,
}