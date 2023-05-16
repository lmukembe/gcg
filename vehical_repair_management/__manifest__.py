# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Repair Management',
    'version': '1.0',
    'summary': 'Allows you to easily manage your vehicle repair workshop.',
    'sequence': 30,
    'description': """This module will help you to manage your vehicle repair / service workshop very easily.
    Main features:
                            
    It has many configuration option, that will make workshop management easier.
    Options like separate and intuitive implementation of vehicles and services configuration.
    
    You can categorize vehicle services.
    Create different Service/Repair Teams by their expertise skills and assign different services to these teams.
    
    To manage the vehicles you have options like vehicle types, brands(make), spare parts, fuel/engine types etc.
    
    There is a feature to auto save a new vehicle by its plate number, and in future it will be used to fetch the 
    vehicle details while create a service work order. This will save your time.
    
    Here we also provide an option to create service templates, You can create these templates and use them to create 
    a service work order very quickly.
    
    In the settings there are options to manage the mail notifications.
    It also gives you the reporting feature and much more.
    odoo workshop app
    Odoo Vehicle Repair
    vehicle Service app
    Vehicle Repair Module                  
    """,
    'category': 'Management',
    'author': 'ErpMstar Solutions',
    'depends': ['hr', 'sale_management'],
    'data': [
        'security/security_group.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/vehicle_service_registration.xml',
        'report/custom_report_layout.xml',
        'report/repair_team_receipt.xml',
        'report/receipt.xml',
        'data/service_sequence.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 49,
    'currency': 'EUR',
    'application': True,
}
