from django.db import models
from django.conf import settings
from questionairesManager.models import Questionnaire, Question, Choice


class SentQuestionnaireRequest(models.Model):
    questionnaire = models.ForeignKey(
        Questionnaire,
        on_delete=models.CASCADE,
        related_name='sent_requests_from_patient'
    )
    specialist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_requests'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_requests'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    is_filled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.questionnaire.name} → {self.patient.get_full_name()}"


class QuestionnaireResponse(models.Model):
    request = models.OneToOneField(
        SentQuestionnaireRequest,
        on_delete=models.CASCADE,
        related_name='response'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Odpowiedź: {self.request.questionnaire.name} – {self.request.patient.get_full_name()}"


class Answer(models.Model):
    response = models.ForeignKey(
        QuestionnaireResponse,
        related_name='answers',
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    # Dla typu TEXT
    text_answer = models.TextField(blank=True, null=True)

    # Dla SINGLE i MULTI choice
    selected_choices = models.ManyToManyField(Choice, blank=True)

    def __str__(self):
        return f"{self.response.request.patient.get_full_name()} – {self.question.question_text}"
