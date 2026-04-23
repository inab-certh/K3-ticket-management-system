#records/models/actions.py
from django.db import models
from django.contrib.auth import get_user_model
from .mixins import TimeStampedModel
from .person import Person
from .request import Request
from django.utils import timezone

User = get_user_model()


class Action(TimeStampedModel):
    """
    Actions taken by K3 staff on behalf of a request.
    Based on Excel: ενέργειες-επαφές tab (up to 20 actions per person).
    """

    ACTION_TYPES = [
        ('CONTACT', 'Επικοινωνία'),      # call or email — medium doesn't matter
        ('REFERRAL', 'Παραπομπή'),        # sent beneficiary or request somewhere
        ('DOCUMENT', 'Έγγραφο'),          # submitted or received a document
        ('FOLLOWUP', 'Παρακολούθηση'),    # internal follow-up / status check
    ]

    DIRECTION_CHOICES = [
        ('TO', 'Προς'),
        ('FROM', 'Από'),
    ]

    # Core relationships
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE,
        related_name='actions', verbose_name='Αίτημα'
    )
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE,
        related_name='actions', verbose_name='Ωφελούμενος'
    )

    # What happened
    action_type = models.CharField(
        'Τύπος ενέργειας', max_length=20,
        choices=ACTION_TYPES, default='CONTACT'
    )
    direction = models.CharField(
        'Κατεύθυνση', max_length=10,
        choices=DIRECTION_CHOICES, blank=True
    )
    action_date = models.DateField('Ημερομηνία', default=timezone.now)

    # Who was contacted — free text, no FK
    org_name = models.CharField('Φορέας', max_length=200, blank=True)
    contact_name = models.CharField('Όνομα επικοινωνίας', max_length=200, blank=True)
    contact_role = models.CharField('Θέση', max_length=100, blank=True)
    contact_phone = models.CharField('Τηλέφωνο', max_length=20, blank=True)
    contact_email = models.EmailField('Email', blank=True)

    # Outcome
    result = models.TextField('Αποτέλεσμα', blank=True)

    # Follow-up
    follow_up_date = models.DateField('Ημερομηνία παρακολούθησης', null=True, blank=True)
    is_completed = models.BooleanField('Ολοκληρώθηκε', default=True)

    performed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Εκτελέστηκε από'
    )

    class Meta:
        ordering = ['-action_date', '-created_at']
        indexes = [
            models.Index(fields=['action_date']),
            models.Index(fields=['request', 'action_date']),
            models.Index(fields=['person', 'action_date']),
            models.Index(fields=['follow_up_date']),
        ]
        verbose_name = 'Ενέργεια'
        verbose_name_plural = 'Ενέργειες'

    def __str__(self):
        action = dict(self.ACTION_TYPES).get(self.action_type, '')
        direction = dict(self.DIRECTION_CHOICES).get(self.direction, '')
        target = self.org_name or self.contact_name or ''
        parts = [p for p in [action, direction, target] if p]
        return ' '.join(parts) or f'Ενέργεια {self.action_date}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.request.number_of_actions = (self.request.number_of_actions or 0) + 1
            self.request.save(update_fields=['number_of_actions'])
        super().save(*args, **kwargs)