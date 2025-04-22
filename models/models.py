# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

class TodoTask(models.Model):
    _name = 'todo.task'
    _description = 'Tarea por hacer'

    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripción')
    is_done = fields.Boolean('¿Completada?', default=False)
    priority = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Normal'),
        ('2', 'Alta'),
        ('3', 'Muy Alta')
    ], string='Prioridad', default='1')
    deadline = fields.Date('Fecha límite')
    user_id = fields.Many2one('res.users', string='Responsable', default=lambda self: self.env.user)
    tag_ids = fields.Many2many('todo.tag', string='Etiquetas')

    # Relaciones para subtareas
    parent_id = fields.Many2one('todo.task', string='Tarea Principal', ondelete='cascade')
    subtask_ids = fields.One2many('todo.task', 'parent_id', string='Subtareas')

    # Campos para el seguimiento de subtareas
    subtask_count = fields.Integer(string='Número de Subtareas', compute='_compute_subtask_count', store=True)
    completed_subtasks = fields.Integer(string='Subtareas Completadas', compute='_compute_completed_subtasks',
                                        store=True)

    # Campo calculado de tipo Float
    completion_rate = fields.Float(
        string='Índice de Finalización',
        compute='_compute_completion_rate',
        store=True,
        digits=(5, 2),
        help='Porcentaje de finalización de la tarea (0-100%)'
    )

    # Añadir en la clase TodoTask
    status_id = fields.Many2one(
        'todo.status',
        string='Estado',
        tracking=True,
        index=True,
        copy=False,
        help="Estado actual de la tarea"
    )
    etapa_id = fields.Many2one('todo.etapa', string='Etapa')

    # Método para contar subtareas
    @api.depends('subtask_ids')
    def _compute_subtask_count(self):
        for task in self:
            task.subtask_count = len(task.subtask_ids)

    # Método para contar subtareas completadas
    @api.depends('subtask_ids', 'subtask_ids.is_done')
    def _compute_completed_subtasks(self):
        for task in self:
            task.completed_subtasks = len(task.subtask_ids.filtered(lambda x: x.is_done))

    # Método modificado para calcular el índice de finalización
    @api.depends('is_done', 'subtask_count', 'completed_subtasks', 'subtask_ids', 'subtask_ids.is_done')
    def _compute_completion_rate(self):
        for task in self:
            # Si la tarea está marcada como completada, siempre es 100%
            if task.is_done:
                task.completion_rate = 100.0
            # Si tiene subtareas, el porcentaje es basado en subtareas completadas
            elif task.subtask_count > 0:
                task.completion_rate = (task.completed_subtasks / task.subtask_count) * 100.0 if task.subtask_count > 0 else 0.0
            # Si no tiene subtareas, el porcentaje es 0% si no está completada
            else:
                task.completion_rate = 0.0

    # Método para marcar una tarea como completada
    def action_done(self):
        for task in self:
            # Verificar si es una tarea principal con subtareas
            if task.subtask_ids:
                # Buscar subtareas pendientes
                pending_subtasks = task.subtask_ids.filtered(lambda x: not x.is_done)

                # Si hay subtareas pendientes, mostrar mensaje
                if pending_subtasks:
                    pending_count = len(pending_subtasks)
                    subtask_names = ", ".join([subtask.name for subtask in pending_subtasks[:3]])

                    # Si hay más de 3 subtareas pendientes, añadir indicador
                    if pending_count > 3:
                        subtask_names += f" y {pending_count - 3} más"

                    # Mensajes para singular o plural
                    if pending_count == 1:
                        message = f"No puedes completar esta tarea porque tiene una subtarea pendiente: {subtask_names}"
                    else:
                        message = f"No puedes completar esta tarea porque tiene {pending_count} subtareas pendientes: {subtask_names}"

                    # Añadir sugerencia
                    message += "\n\nPor favor, completa todas las subtareas antes de marcar esta tarea como completada."

                    raise UserError(message)

            # Si pasa la validación o no tiene subtareas, marcar como completada
            task.is_done = True

        return True

    # Método para marcar una tarea como pendiente
    def action_undone(self):
        for task in self:
            task.is_done = False
        return True

    # Nuevo método para crear subtareas
    def action_add_subtask(self):
        self.ensure_one()
        return {
            'name': 'Añadir Subtarea',
            'type': 'ir.actions.act_window',
            'res_model': 'todo.task',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_id': self.id,
                'default_user_id': self.user_id.id,
            },
        }

class TodoStatus(models.Model):
    _name = 'todo.status'
    _description = 'Estado de la Tarea'
    _order = 'sequence, id'

    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripción')
    color = fields.Integer('Color', default=0)
    sequence = fields.Integer('Secuencia', default=10)
    active = fields.Boolean('Activo', default=True)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'El nombre del estado debe ser único.')
    ]

class TodoTag(models.Model):
    _name = 'todo.tag'
    _description = 'Etiqueta para tareas'

    name = fields.Char('Nombre', required=True)
    color = fields.Char('Color', default="1")  # Valor por defecto negro

class TodoDashboard(models.Model):
    _name = 'todo.dashboard'
    _description = 'Dashboard de Tareas'

    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripción')
    active = fields.Boolean('Activo', default=True)
    user_ids = fields.Many2many('res.users', string='Usuarios')
    etapa_ids = fields.One2many('todo.etapa', 'dashboard_id', string='Etapas')

    def action_view_etapas(self):
        self.ensure_one()
        return {
            'name': 'Tablero: ' + self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'todo.task',
            'view_mode': 'kanban,tree,form',
            'domain': [('etapa_id.dashboard_id', '=', self.id)],
            'context': {
                'default_dashboard_id': self.id,
                'group_by': 'etapa_id',
            }
        }

class TodoEtapa(models.Model):
    _name = 'todo.etapa'
    _description = 'Etapas de Tareas'
    _order = 'sequence'

    name = fields.Char('Nombre', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    dashboard_id = fields.Many2one('todo.dashboard', string='Dashboard', required=True)
    task_ids = fields.One2many('todo.task', 'etapa_id', string='Tareas')
    fold = fields.Boolean('Plegada')
    active = fields.Boolean('Activo', default=True)
