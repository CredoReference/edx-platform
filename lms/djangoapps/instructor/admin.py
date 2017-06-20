from django.contrib import admin
from lms.djangoapps.instructor.models import InstructorAvailableSections
from django_extensions.admin import ForeignKeyAutocompleteAdmin


def available_sections_bulk_action(field, is_set):
    prefix = 'Set' if is_set else 'Unset'
    name = field.name.__str__()

    def action(modeladmin, request, queryset):
        queryset.update(**{name: is_set})

    action.short_description = prefix + ' [' + field.verbose_name + '] for selected objects'
    action.__name__ = prefix + name
    return action


class InstructorAvailableSectionsAdmin(ForeignKeyAutocompleteAdmin):
    bulk_fields_names = ['show_course_info', 'show_membership', 'show_cohort', 'show_student_admin',
                         'show_data_download', 'show_email', 'show_analytics', 'show_studio_link',
                         'show_open_responses']

    list_display = ['user'] + bulk_fields_names

    model_fields = InstructorAvailableSections._meta.get_fields()
    bulk_fields = [field for field in model_fields if field.name.__str__() in bulk_fields_names]

    bulk_set_actions = [available_sections_bulk_action(field, is_set=True) for field in bulk_fields]
    bulk_unset_actions = [available_sections_bulk_action(field, is_set=False) for field in bulk_fields]

    actions = bulk_set_actions + bulk_unset_actions
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')

    related_search_fields = {
        'user': ('email', 'username', 'first_name', 'last_name'),
    }

admin.site.register(InstructorAvailableSections, InstructorAvailableSectionsAdmin)
