# records/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.db.models import Count, Q, Max
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import (
    Action, Person, Request, Region, RegionalUnit, Municipality,
    RequestTag, RequestStatus, RequestCategory, Center,
    Neoplasm, Therapy, MedicalHistory,ICD10Category, ICD10Subcategory, ICD10Code,
)
from .forms.person import PersonForm
from .forms.request import RequestForm
from .forms.action import ActionForm
from .forms.step1_basic import BeneficiaryForm, Step1RequestForm
from .forms.step2_additional import BeneficiaryExtraForm
from .forms.step2_contact import ContactPersonForm
from .forms.step3_employment import Step3Form
from .forms.step5_history import Step5MedicalHistoryForm, Step5ComorbidityForm, Step5BMIForm

import json


User = get_user_model()


# ---------- Alerts helper ----------
def get_alerts():
    today = timezone.now().date()
    three_months = today + timedelta(days=90)
    thirty_days_ago = today - timedelta(days=30)

    kepa_expired = MedicalHistory.objects.filter(
        kepa_check=True, kepa_expiry__lt=today
    ).count()

    kepa_expiring = MedicalHistory.objects.filter(
        kepa_check=True, kepa_expiry__gte=today, kepa_expiry__lte=three_months
    ).count()

    overdue_requests = Request.objects.filter(
        status__is_closed=False, due_date__lt=today
    ).count()

    stale_requests = Request.objects.filter(
        status__is_closed=False
    ).annotate(
        last_action=Max('actions__action_date')
    ).filter(
        Q(last_action__lt=thirty_days_ago) | Q(last_action__isnull=True),
        created_at__date__lt=thirty_days_ago
    ).count()

    incomplete_profiles = Person.objects.filter(
        Q(amka__isnull=True) | Q(amka='') |
        Q(mobile='') |
        Q(insurance_status='')
    ).count()

    no_requests = Person.objects.filter(
        requests__isnull=True,
        created_at__date__lt=thirty_days_ago
    ).count()

    return {
        'alert_kepa_expired': kepa_expired,
        'alert_kepa_expiring': kepa_expiring,
        'alert_overdue_requests': overdue_requests,
        'alert_stale_requests': stale_requests,
        'alert_incomplete_profiles': incomplete_profiles,
        'alert_no_requests': no_requests,
        'total_alerts': kepa_expired + kepa_expiring + overdue_requests + stale_requests + incomplete_profiles + no_requests,
    }


# ---------- Auth ----------
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Η εγγραφή ήταν επιτυχής. Καλώς ήρθατε!")
            return redirect("dashboard")
        else:
            messages.error(request, "Υπήρξε πρόβλημα με τη φόρμα. Ελέγξτε τα στοιχεία.")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


# ---------- Dashboard ----------
@login_required
def dashboard(request):
    total_persons = Person.objects.count()
    total_requests = Request.objects.count()
    open_requests = Request.objects.filter(status__is_closed=False).count()
    recent_persons = Person.objects.order_by('-created_at')[:5]
    recent_requests = Request.objects.select_related(
        'person', 'status'
    ).order_by('-created_at')[:5]

    context = {
        "total_persons": total_persons,
        "total_requests": total_requests,
        "open_requests": open_requests,
        "recent_persons": recent_persons,
        "recent_requests": recent_requests,
    }
    context.update(get_alerts())
    return render(request, "records/dashboard.html", context)


# ---------- New Entry Wizard ----------
@login_required
def new_entry(request):
    step_raw = request.POST.get('current_step') or request.GET.get('step', '1')
    beneficiary_id = request.POST.get('beneficiary_id') or request.GET.get('beneficiary_id') or None

    person = None
    if beneficiary_id and beneficiary_id != 'None':
        try:
            person = Person.objects.get(pk=beneficiary_id)
        except (Person.DoesNotExist, ValueError):
            person = None

    if request.method == 'POST':
        action = request.POST.get('action')
        step = int(step_raw) if step_raw not in ('finish',) else 5

        # Handle prev navigation — just redirect without saving
        if action == 'prev':
            return redirect(f"{reverse('new_entry')}?step={step - 1}&beneficiary_id={beneficiary_id}&request_id={request.POST.get('request_id', '')}")

        # Handle exit from any step
        if action == 'exit' and person:
            messages.success(request, "Η εγγραφή αποθηκεύτηκε.")
            return redirect('person_detail', pk=person.pk)

        if action == 'finish':
            if person:
                mh, _ = MedicalHistory.objects.get_or_create(person=person)
                mh.kepa_check = bool(request.POST.get('kepa_check'))
                kepa_expiry = request.POST.get('kepa_expiry')
                if kepa_expiry:
                    mh.kepa_expiry = kepa_expiry
                mh.disability = bool(request.POST.get('disability'))
                mh.save()
            messages.success(request, "Η εγγραφή ολοκληρώθηκε.")
            return redirect('person_detail', pk=person.pk)

        if step == 1:
            b_form = BeneficiaryForm(request.POST, instance=person)
            request_id = request.POST.get('request_id') or request.GET.get('request_id')
            existing_request = None
            if request_id:
                try:
                    existing_request = Request.objects.get(pk=request_id, person=person)
                except (Request.DoesNotExist, ValueError):
                    pass
            elif person:
                existing_request = person.requests.order_by('created_at').first()

            r_form = Step1RequestForm(request.POST, instance=existing_request)

            if b_form.is_valid() and r_form.is_valid():
                person = b_form.save()
                req = r_form.save(commit=False)
                req.person = person
                req.created_by = request.user
                if not req.pk:
                    req.status = RequestStatus.objects.get(id=1)
                    req.is_intake = True
                req.save()
                base_url = f"{reverse('new_entry')}?beneficiary_id={person.pk}&request_id={req.pk}"
                if action == 'next':
                    return redirect(f"{base_url}&step=2")
                elif action == 'exit':
                    messages.success(request, "Η εγγραφή αποθηκεύτηκε.")
                    return redirect('person_detail', pk=person.pk)
                else:  # draft
                    messages.success(request, "Αποθηκεύτηκε ως πρόχειρο.")
                    return redirect(f"{base_url}&step=1")
            else:
                print("=== FORM ERRORS ===")
                print("b_form:", b_form.errors)
                print("r_form:", r_form.errors)
                return render(request, 'records/newentry.html', {
                    'step': 1,
                    'beneficiary_id': beneficiary_id,
                    'request_id': request_id,
                    'beneficiary_form': b_form,
                    'request_form': r_form,
                    'person': person,
                })

        if step == 2:
            request_id = request.POST.get('request_id') or request.GET.get('request_id')
            s2_form = BeneficiaryExtraForm(request.POST, instance=person)
            third_contact = request.POST.get('third_contact')

            # Load existing contact for update if exists
            existing_contact = person.contacts.first() if person else None
            contact_form = ContactPersonForm(request.POST, instance=existing_contact)

            if s2_form.is_valid():
                s2_form.save()
                if third_contact and contact_form.is_valid():
                    contact = contact_form.save(commit=False)
                    contact.person = person
                    contact.save()
                base_url = f"{reverse('new_entry')}?beneficiary_id={person.pk}&request_id={request_id}"
                if action == 'next':
                    return redirect(f"{base_url}&step=3")
                elif action == 'exit':
                    messages.success(request, "Η εγγραφή αποθηκεύτηκε.")
                    return redirect('person_detail', pk=person.pk)
                else:  # draft
                    messages.success(request, "Αποθηκεύτηκε ως πρόχειρο.")
                    return redirect(f"{base_url}&step=2")
            return render(request, 'records/newentry.html', {
                'step': 2,
                'beneficiary_id': beneficiary_id,
                'request_id': request_id,
                'beneficiary_form': BeneficiaryForm(instance=person),
                'step2_form': s2_form,
                'contact_form': contact_form,
                'third_contact': third_contact,
                'person': person,
            })
        if step == 3:
            request_id = request.POST.get('request_id') or request.GET.get('request_id')
            step3_form = Step3Form(request.POST, instance=person)
            if step3_form.is_valid():
                step3_form.save()
                base_url = f"{reverse('new_entry')}?beneficiary_id={person.pk}&request_id={request_id}"
                if action == 'next':
                    return redirect(f"{base_url}&step=4")
                elif action == 'exit':
                    messages.success(request, "Η εγγραφή αποθηκεύτηκε.")
                    return redirect('person_detail', pk=person.pk)
                else:
                    messages.success(request, "Αποθηκεύτηκε ως πρόχειρο.")
                    return redirect(f"{base_url}&step=3")
            return render(request, 'records/newentry.html', {
                'step': 3,
                'beneficiary_id': beneficiary_id,
                'request_id': request_id,
                'beneficiary_form': BeneficiaryForm(instance=person),
                'step3_form': step3_form,
                'person': person,
            })
        if step == 4:
            request_id = request.POST.get('request_id') or request.GET.get('request_id')
            print("=== STEP 4 POST ===")
            print("POST keys:", [k for k in request.POST.keys()])
            if person:
                person.neoplasms.all().delete()
                i = 0
                while True:
                    category = request.POST.get(f'category_id_{i}')
                    print(f"category_id_{i}:", category)
                    if category is None:
                        break
                    icd10_label = request.POST.get(f'icd10_{i}', '')
                    neoplasm = Neoplasm.objects.create(
                        person=person,
                        icd10_category_id=request.POST.get(f'category_id_{i}') or None,
                        icd10_subcategory_id=request.POST.get(f'subcategory_id_{i}') or None,
                        icd10_code_id=request.POST.get(f'icd10_id_{i}') or None,
                        localization=request.POST.get(f'localization_{i}', ''),
                        metastasis=bool(request.POST.get(f'metastasis_{i}')),
                        surgery=bool(request.POST.get(f'surgery_{i}')),
                        surgery_hospital=request.POST.get(f'surgery_hospital_{i}', ''),
                        scheduled_surgery=bool(request.POST.get(f'scheduled_surgery_{i}')),
                    )
                    # Save therapies
                    if request.POST.get(f'has_therapies_{i}'):
                        j = 0
                        while True:
                            therapy_type = request.POST.get(f'therapy_type_{i}_{j}')
                            if therapy_type is None:
                                break
                            if therapy_type:
                                Therapy.objects.create(
                                    neoplasm=neoplasm,
                                    therapy_type=therapy_type,
                                    hospital_name=request.POST.get(f'therapy_hospital_{i}_{j}', ''),
                                )
                            j += 1
                    i += 1
            
            base_url = f"{reverse('new_entry')}?beneficiary_id={person.pk}&request_id={request_id}"
            if action == 'next':
                return redirect(f"{base_url}&step=5")
            elif action == 'exit':
                messages.success(request, "Η εγγραφή αποθηκεύτηκε.")
                return redirect('person_detail', pk=person.pk)
            else:
                messages.success(request, "Αποθηκεύτηκε ως πρόχειρο.")
                return redirect(f"{base_url}&step=4")
        if step == 5:
            request_id = request.POST.get('request_id') or request.GET.get('request_id')
            if person:
                mh, _ = MedicalHistory.objects.get_or_create(person=person)
                mh_form = Step5MedicalHistoryForm(request.POST, instance=mh)
                from .models import Comorbidity
                comorbidity, _ = Comorbidity.objects.get_or_create(person=person)
                comorbidity_form = Step5ComorbidityForm(request.POST, instance=comorbidity)
                bmi_form = Step5BMIForm(request.POST, instance=person)

                if mh_form.is_valid() and comorbidity_form.is_valid() and bmi_form.is_valid():
                    mh_form.save()
                    comorbidity_form.save()
                    bmi_form.save()
                    base_url = f"{reverse('new_entry')}?beneficiary_id={person.pk}&request_id={request_id}"
                    if action == 'finish':
                        messages.success(request, "Η εγγραφή ολοκληρώθηκε.")
                        return redirect('person_detail', pk=person.pk)
                    elif action == 'exit':
                        messages.success(request, "Η εγγραφή αποθηκεύτηκε.")
                        return redirect('person_detail', pk=person.pk)
                    else:  # draft
                        messages.success(request, "Αποθηκεύτηκε ως πρόχειρο.")
                        return redirect(f"{base_url}&step=5")
                return render(request, 'records/newentry.html', {
                    'step': 5,
                    'beneficiary_id': beneficiary_id,
                    'request_id': request_id,
                    'beneficiary_form': BeneficiaryForm(instance=person),
                    'mh_form': mh_form,
                    'comorbidity_form': comorbidity_form,
                    'bmi_form': bmi_form,
                    'person': person,
                })

        # Steps 4–5 stub — just advance/stay
        if action == 'next':
            return redirect(f"{reverse('new_entry')}?step={step + 1}&beneficiary_id={beneficiary_id}")
        else:
            messages.success(request, "Αποθηκεύτηκε ως πρόχειρο.")
            return redirect(f"{reverse('new_entry')}?step={step}&beneficiary_id={beneficiary_id}")

    # GET
    step = int(step_raw) if step_raw != 'finish' else 1
    b_form = BeneficiaryForm(instance=person)

    request_id = request.GET.get('request_id')
    existing_request = None
    if request_id:
        try:
            existing_request = Request.objects.get(pk=request_id)
        except (Request.DoesNotExist, ValueError):
            pass
    elif person:
        existing_request = person.requests.order_by('created_at').first()
        if existing_request:
            request_id = existing_request.pk

    r_form = Step1RequestForm(instance=existing_request)
    s2_form = BeneficiaryExtraForm(instance=person)

    existing_contact = person.contacts.first() if person else None
    contact_form = ContactPersonForm(instance=existing_contact)
    third_contact = 'yes' if existing_contact else None
    
    step3_form = Step3Form(instance=person)
    mh = getattr(person, 'medical_history', None) if person else None
    comorbidity = getattr(person, 'comorbidity', None) if person else None
    mh_form = Step5MedicalHistoryForm(instance=mh)
    comorbidity_form = Step5ComorbidityForm(instance=comorbidity)
    bmi_form = Step5BMIForm(instance=person)
    
    icd10_categories = list(ICD10Category.objects.values('id', 'name'))
    icd10_subcategories = list(ICD10Subcategory.objects.values('id', 'name', 'category_id'))
    icd10_codes = list(ICD10Code.objects.values('id', 'code', 'label', 'subcategory_id'))
    
    existing_neoplasms = []
    if person:
        for n in person.neoplasms.all():
            existing_neoplasms.append({
                'category_id': n.icd10_category_id,
                'subcategory_id': n.icd10_subcategory_id,
                'icd10_id': n.icd10_code_id,
                'localization': n.localization or '',
                'metastasis': n.metastasis,
                'surgery': n.surgery,
                'surgery_hospital': n.surgery_hospital or '',
                'scheduled_surgery': n.scheduled_surgery,
            })

    return render(request, 'records/newentry.html', {
        'step': step,
        'beneficiary_id': beneficiary_id,
        'request_id': request_id,
        'beneficiary_form': b_form,
        'request_form': r_form,
        'step2_form': s2_form,
        'contact_form': contact_form,
        'third_contact': third_contact,
        'person': person,
        'step3_form': step3_form,
        'icd10_categories_json': json.dumps(icd10_categories),
        'icd10_subcategories_json': json.dumps(icd10_subcategories),
        'icd10_codes_json': json.dumps(icd10_codes),
        'existing_neoplasms_json': json.dumps(existing_neoplasms),
        'mh_form': mh_form,
        'comorbidity_form': comorbidity_form,
        'bmi_form': bmi_form,
    })


# ---------- Person CRUD ----------
class PersonListView(LoginRequiredMixin, ListView):
    model = Person
    template_name = "persons/person_list.html"
    context_object_name = "persons"
    paginate_by = 20

    def get_queryset(self):
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        qs = Person.objects.all().select_related(
            'municipality__regional_unit__region'
        ).annotate(
            total_requests=Count('requests', distinct=True),
            open_requests=Count(
                'requests',
                filter=Q(requests__status__is_closed=False),
                distinct=True
            ),
            last_action_date=Max('actions__action_date'),
        )

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(last_name__icontains=q) |
                Q(first_name__icontains=q) |
                Q(amka__icontains=q)
            )

        alert = self.request.GET.get("alert")
        if alert == "kepa_expired":
            qs = qs.filter(
                medicalhistory__kepa_check=True,
                medicalhistory__kepa_expiry__lt=today
            )
        elif alert == "kepa_expiring":
            qs = qs.filter(
                medicalhistory__kepa_check=True,
                medicalhistory__kepa_expiry__gte=today,
                medicalhistory__kepa_expiry__lte=today + timedelta(days=90)
            )
        elif alert == "incomplete":
            qs = qs.filter(
                Q(amka__isnull=True) | Q(amka='') |
                Q(mobile='') | Q(insurance_status='')
            )
        elif alert == "no_requests":
            qs = qs.filter(
                requests__isnull=True,
                created_at__date__lt=thirty_days_ago
            )

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_alerts())
        context['active_alert'] = self.request.GET.get('alert', '')
        return context


class PersonCreateView(LoginRequiredMixin, CreateView):
    model = Person
    form_class = PersonForm
    template_name = "persons/person_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Το άτομο δημιουργήθηκε επιτυχώς.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("person_list")


class PersonDetailView(LoginRequiredMixin, DetailView):
    model = Person
    template_name = "persons/person_detail.html"
    context_object_name = "person"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_requests'] = self.object.requests.filter(
            is_intake=False
        ).select_related('status').order_by('-created_at')[:10]
        context['documents'] = self.object.documents.order_by('-created_at')[:5]
        context['contact_persons'] = self.object.contacts.order_by('-is_primary')
        return context


class PersonUpdateView(LoginRequiredMixin, UpdateView):
    model = Person
    form_class = PersonForm
    template_name = "persons/person_form.html"

    def get(self, request, *args, **kwargs):
        person = self.get_object()
        existing_request = person.requests.order_by('created_at').first()
        base_url = reverse('new_entry')
        url = f"{base_url}?step=1&beneficiary_id={person.pk}"
        if existing_request:
            url += f"&request_id={existing_request.pk}"
        return redirect(url)

    def form_valid(self, form):
        messages.success(self.request, "Τα στοιχεία ενημερώθηκαν επιτυχώς.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("person_detail", kwargs={'pk': self.object.pk})


class PersonDeleteView(LoginRequiredMixin, DeleteView):
    model = Person
    template_name = "persons/person_confirm_delete.html"
    success_url = reverse_lazy("person_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Το άτομο διαγράφηκε επιτυχώς.")
        return super().delete(request, *args, **kwargs)


# ---------- Request CRUD ----------
class RequestListView(LoginRequiredMixin, ListView):
    model = Request
    template_name = "requests/request_list.html"
    context_object_name = "requests"
    paginate_by = 20

    def get_queryset(self):
        today = timezone.now().date()
        qs = Request.objects.filter(is_intake=False).select_related(
            "person", "status", "category", "assigned_to"
        ).prefetch_related("tags")

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(person__last_name__icontains=q) |
                Q(person__first_name__icontains=q) |
                Q(subject__icontains=q)
            )

        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status_id=status)

        priority = self.request.GET.get("priority")
        if priority:
            qs = qs.filter(priority=priority)

        assigned = self.request.GET.get("assigned")
        if assigned:
            qs = qs.filter(assigned_to_id=assigned)

        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(tags__id=tag)

        overdue = self.request.GET.get("overdue")
        if overdue:
            qs = qs.filter(status__is_closed=False, due_date__lt=today)

        return qs.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = RequestStatus.objects.all()
        context['priorities'] = Request.PRIORITY_CHOICES
        context['tags'] = RequestTag.objects.filter(is_active=True).order_by('category', 'name')
        context['users'] = User.objects.filter(is_active=True)
        context['current_filters'] = {
            'q': self.request.GET.get('q', ''),
            'status': self.request.GET.get('status', ''),
            'priority': self.request.GET.get('priority', ''),
            'assigned': self.request.GET.get('assigned', ''),
            'tag': self.request.GET.get('tag', ''),
            'overdue': self.request.GET.get('overdue', ''),
        }
        return context


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = Request
    template_name = "requests/request_detail.html"
    context_object_name = "request_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = self.object.actions.select_related(
            'performed_by'
        ).order_by('-action_date')
        context['attachments'] = self.object.attachments.order_by('-created_at')
        return context


class RequestCreateView(LoginRequiredMixin, CreateView):
    model = Request
    form_class = RequestForm
    template_name = "requests/request_form.html"

    def get_initial(self):
        initial = super().get_initial()
        person_id = self.request.GET.get("person")
        if person_id:
            initial["person"] = person_id
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Το αίτημα δημιουργήθηκε επιτυχώς.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={'pk': self.object.pk})


class RequestUpdateView(LoginRequiredMixin, UpdateView):
    model = Request
    form_class = RequestForm
    template_name = "requests/request_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Το αίτημα ενημερώθηκε επιτυχώς.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={'pk': self.object.pk})


class RequestDeleteView(LoginRequiredMixin, DeleteView):
    model = Request
    template_name = "requests/request_confirm_delete.html"
    success_url = reverse_lazy("request_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Το αίτημα διαγράφηκε επιτυχώς.")
        return super().delete(request, *args, **kwargs)


# ---------- Actions ----------
class ActionCreateView(LoginRequiredMixin, CreateView):
    model = Action
    form_class = ActionForm
    template_name = "actions/action_form.html"

    def get_initial(self):
        initial = super().get_initial()
        initial['action_date'] = timezone.now().date()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_obj'] = get_object_or_404(Request, pk=self.kwargs['request_pk'])
        return context

    def form_valid(self, form):
        request_obj = get_object_or_404(Request, pk=self.kwargs['request_pk'])
        form.instance.request = request_obj
        form.instance.person = request_obj.person
        form.instance.performed_by = self.request.user
        messages.success(self.request, "Η ενέργεια καταχωρήθηκε.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={'pk': self.kwargs['request_pk']})


class ActionUpdateView(LoginRequiredMixin, UpdateView):
    model = Action
    form_class = ActionForm
    template_name = "actions/action_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request_obj'] = self.object.request
        return context

    def form_valid(self, form):
        messages.success(self.request, "Η ενέργεια ενημερώθηκε.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("request_detail", kwargs={'pk': self.object.request.pk})


# ---------- Geography API ----------
class RegionalUnitsAPIView(View):
    def get(self, request):
        region_id = request.GET.get('region_id')
        if not region_id:
            return JsonResponse({'units': []})
        try:
            region = Region.objects.get(id=region_id)
            units = region.regional_units.all().values('id', 'name').order_by('sort_order', 'name')
            return JsonResponse({'units': list(units)})
        except Region.DoesNotExist:
            return JsonResponse({'units': []})


class MunicipalitiesAPIView(View):
    def get(self, request):
        unit_id = request.GET.get('unit_id')
        if not unit_id:
            return JsonResponse({'municipalities': []})
        try:
            unit = RegionalUnit.objects.get(id=unit_id)
            municipalities = unit.municipalities.all().values('id', 'name').order_by('sort_order', 'name')
            return JsonResponse({'municipalities': list(municipalities)})
        except RegionalUnit.DoesNotExist:
            return JsonResponse({'municipalities': []})


# ---------- Statistics ----------
@login_required
def statistics_view(request):
    total_beneficiaries = Person.objects.count()

    gender_stats = Person.objects.values('gender').annotate(
        count=Count('id')
    ).order_by('gender')

    communication_stats = Request.objects.values(
        'communication_method'
    ).annotate(count=Count('id')).order_by('-count')

    status_stats = Request.objects.values(
        'status__name'
    ).annotate(count=Count('id')).order_by('-count')

    insurance_stats = Person.objects.values(
        'insurance_status'
    ).annotate(count=Count('id')).order_by('-count')

    tag_stats = RequestTag.objects.annotate(
        usage=Count('request')
    ).order_by('-usage')[:10]

    context = {
        'total_beneficiaries': total_beneficiaries,
        'gender_stats': gender_stats,
        'communication_stats': communication_stats,
        'status_stats': status_stats,
        'insurance_stats': insurance_stats,
        'tag_stats': tag_stats,
    }
    return render(request, "records/statistics.html", context)


# ---------- Misc ----------
def settings_view(request):
    return render(request, "includes/settings-box.html")


# ---------- Quick Search API ----------
class QuickSearchAPIView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if len(q) < 2:
            return JsonResponse({'results': []})

        persons = Person.objects.filter(
            Q(last_name__icontains=q) |
            Q(first_name__icontains=q) |
            Q(amka__icontains=q)
        ).values('id', 'last_name', 'first_name', 'amka')[:10]

        results = [
            {
                'id': p['id'],
                'text': f"{p['last_name']} {p['first_name']} ({p['amka'] or 'Χωρίς ΑΜΚΑ'})",
                'name': f"{p['last_name']} {p['first_name']}"
            }
            for p in persons
        ]
        return JsonResponse({'results': results})