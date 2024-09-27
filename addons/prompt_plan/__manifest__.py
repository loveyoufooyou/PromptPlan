{
    'name': 'Prompt Plan',
    'version': '1.0',
    'description': """
Prompt Plan
===========
This module provides an AI Prompt Plan, which is designed to set goals, record the history of the Prompt, and better manage the Prompt.
""",
    'summary': 'Prompt Plan',
    'author': 'Chaox',
    'website': 'https://github.com/loveyoufooyou/PromptPlan',
    'license': 'LGPL-3',
    'category': 'Prompt/PromptPlan',
    'depends': ['base', 'web'],
    'data': [
        'security/prompt_plan_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/base_view.xml',
        'views/prompt_template_view.xml',
        'views/prompt_plant_menuitem.xml',
        'wizard/prompt_template_test_save_wizard.xml',
    ],
    'demo': [],
    'auto_install': False,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'prompt_plan/static/src/**/*',
        ],
    }
}