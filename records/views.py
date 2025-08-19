# records/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

#from .forms.register import RegisterForm
from .models import (
    Person, Request, Region, RegionalUnit, Municipality, 
    RequestTag, RequestStatus, RequestCategory, Center
)
#from .forms.person import PersonForm
#from .forms.request import RequestForm
PersonForm = None  
RequestForm = None

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
    
    # Add some statistics for the dashboard
    try:
        open_requests = Request.objects.filter(status__is_closed=False).count()
    except:
        open_requests = 0
        
    recent_persons = Person.objects.order_by('-created_at')[:5]
    recent_requests = Request.objects.select_related('person', 'status').order_by('-created_at')[:5]
    
    return render(request, "records/dashboard.html", {
        "total_persons": total_persons,
        "total_requests": total_requests,
        "open_requests": open_requests,
        "recent_persons": recent_persons,
        "recent_requests": recent_requests,
    })


# ---------- Person CRUD ----------
class PersonListView(LoginRequiredMixin, ListView):
    model = Person
    template_name = "persons/person_list.html"
    context_object_name = "persons"
    paginate_by = 20

    def get_queryset(self):
        qs = Person.objects.all()
        # Add select_related when municipality model is ready
        try:
            qs = qs.select_related('municipality__regional_unit__region')
        except:
            pass  # Handle case where geography models aren't set up yet
            
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                last_name__icontains=q
            ) | qs.filter(
                first_name__icontains=q
            ) | qs.filter(
                amka__icontains=q
            )
        return qs.order_by("-created_at")


class PersonCreateView(LoginRequiredMixin, CreateView):
    model = Person
    #form_class = PersonForm
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
        # Add related data
        context['requests'] = self.object.requests.select_related('status').order_by('-created_at')[:10]
        context['documents'] = self.object.documents.order_by('-created_at')[:5]
        return context


class PersonUpdateView(LoginRequiredMixin, UpdateView):
    model = Person
    #form_class = PersonForm
    template_name = "persons/person_form.html"

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
        qs = Request.objects.select_related("person", "status", "center")
        
        # Add prefetch_related for tags when ready
        try:
            qs = qs.prefetch_related("tags")
        except:
            pass  # Handle case where tag system isn't fully set up yet
        
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                person__last_name__icontains=q
            ) | qs.filter(
                person__first_name__icontains=q
            ) | qs.filter(
                subject__icontains=q
            )
        
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status_id=status)
            
        primary_category = self.request.GET.get("category")
        if primary_category:
            qs = qs.filter(primary_category=primary_category)
            
        assigned = self.request.GET.get("assigned")
        if assigned:
            qs = qs.filter(assigned_to_id=assigned)
            
        return qs.order_by("-created_at")


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = Request
    template_name = "requests/request_detail.html"
    context_object_name = "request_obj"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add related actions
        context['actions'] = self.object.actions.select_related(
            'external_org', 'contact_person'
        ).order_by('-action_date')
        context['attachments'] = self.object.attachments.order_by('-created_at')
        return context


class RequestCreateView(LoginRequiredMixin, CreateView):
    model = Request
    #form_class = RequestForm
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
    #form_class = RequestForm
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


# ---------- Geography API (AJAX endpoints) ----------
class RegionalUnitsAPIView(View):
    """AJAX endpoint to get regional units for a region"""
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
    """AJAX endpoint to get municipalities for a regional unit"""
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


# ---------- Statistics/Reports ----------
@login_required
def statistics_view(request):
    """Statistics page matching your Excel dashboard"""
    from django.db.models import Count, Q
    
    # Demographics
    total_beneficiaries = Person.objects.count()
    
    # Gender breakdown
    gender_stats = Person.objects.values('gender').annotate(
        count=Count('id')
    ).order_by('gender')
    
    # Age statistics (you'll need to calculate age properly)
    # This is a simplified version
    age_stats = {
        'mean': 58.7,  # You'd calculate this from birth_year/birth_date
        'median': 59,
        'min': 43,
        'max': 78
    }
    
    # Communication method stats
    communication_stats = Request.objects.values('communication_method').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Request status stats
    status_stats = Request.objects.values('status__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Primary category stats
    category_stats = Request.objects.values('primary_category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Insurance stats
    insurance_stats = Person.objects.values('insurance__insurance_status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_beneficiaries': total_beneficiaries,
        'gender_stats': gender_stats,
        'age_stats': age_stats,
        'communication_stats': communication_stats,
        'status_stats': status_stats,
        'category_stats': category_stats,
        'insurance_stats': insurance_stats,
    }
    
    return render(request, "records/statistics.html", context)


# ---------- Misc ----------
def settings_view(request):
    return render(request, "includes/settings-box.html")


# ---------- Quick Search API ----------
class QuickSearchAPIView(View):
    """AJAX endpoint for quick person search"""
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if len(q) < 2:
            return JsonResponse({'results': []})
        
        persons = Person.objects.filter(
            Q(last_name__icontains=q) |
            Q(first_name__icontains=q) |
            Q(amka__icontains=q)
        ).values('id', 'last_name', 'first_name', 'amka')[:10]
        
        results = []
        for person in persons:
            results.append({
                'id': person['id'],
                'text': f"{person['last_name']} {person['first_name']} ({person['amka'] or 'Χωρίς ΑΜΚΑ'})",
                'name': f"{person['last_name']} {person['first_name']}"
            })
        
        return JsonResponse({'results': results})