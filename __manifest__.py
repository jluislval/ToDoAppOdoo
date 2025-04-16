# -*- coding: utf-8 -*-
{
    'name': 'TodoApp: Cosas por Hacer',
    'summary': 'Gestiona tus tareas y actividades pendientes',
    'description': """
        Módulo para gestionar una lista de tareas por hacer:
        - Crea nuevas tareas con fechas límite
        - Asigna tareas a usuarios
        - Marca tareas como completadas
        - Organiza tareas por etiquetas
    """,
    'author': 'Jose Luis Lopez',
    'website': 'https://didcom.com.mx',
    'category': 'Productivity',
    'version': '15.0.1.0.0',
    'depends': ['base'],
    'data': [
        'security/todoapp_security.xml',
        'security/ir.model.access.csv',
        'views/todo_view.xml',
        'views/todo_menu.xml',
        'views/templates.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
