{
    'name': 'Loan Service Management',
    'version': '17.0.0.0.0',
    'summary': 'Manage loan services for customers',
    'author': 'Eng. Omar Crespo Carrazana',
    'category': 'Services',
    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'data/cron_jobs.xml',
        'views/loan_service_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
}
