from django.db import transaction
from django.db.utils import IntegrityError

from lms.djangoapps.instructor_task.tasks_helper.module_state import update_reset_progress
from lti_provider.models import LtiContextId, LTI1p1
from xmodule.modulestore.django import modulestore


def check_and_reset_lti_user_progress(context_id, user, course_key, usage_key, lti_version=None):
    if not lti_version:
        lti_version = LTI1p1
    if context_id:
        try:
            context = LtiContextId.objects.get(
                course_key=course_key,
                usage_key=usage_key,
                user=user,
                lti_version=lti_version
            )
            if context.value != context_id:
                context.value = context_id
                context.save()
                with modulestore().bulk_operations(course_key):
                    block = modulestore().get_item(usage_key)
                    update_reset_progress(user, course_key, block)
        except LtiContextId.DoesNotExist:
            try:
                with transaction.atomic():
                    context = LtiContextId(
                        user=user,
                        course_key=course_key,
                        usage_key=usage_key,
                        value=context_id,
                        lti_version=lti_version
                    )
                    context.save()
            except IntegrityError:
                pass
