# records/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import JsonResponse
from django.urls import path
from django import forms
from django.db import models
import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta



# Import all models
from .models import (
    # Person related
    Person, ContactPerson,
    # Medical
    MedicalHistory, Neoplasm, Therapy, Comorbidity,
    # Requests
    Request, RequestTag, RequestAttachment,
    # Actions
    Action,
    # Organizations
    Center, ExternalOrganization, Contact,
    # Documents
    Document, DocumentType,
    # Medical codes
    ICD10Code, ICD10Category, ICD10Subcategory,
    # Geography
    Region, RegionalUnit, Municipality,
    # Lookups
    RequestType, RequestStatus, RequestCategory,
    InsuranceProvider, EmploymentStatus, TherapyType
)

# Comment out form imports for now
# try:
#     from .forms.neoplasm import NeoplasmForm
#     from .forms.therapy import TherapyForm
#     from .forms.request import RequestForm
# except ImportError:
    # Use default forms if custom forms don't exist yet
NeoplasmForm = None
TherapyForm = None
RequestForm = None

# ========== INLINES ==========

class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 1
    fields = ('last_name', 'first_name', 'relation', 'address', 'city', 'postal_code', 'municipality', 'landline', 'mobile', 'email', 'is_primary')
    autocomplete_fields = ['municipality']

class MedicalHistoryInline(admin.StackedInline):
    model = MedicalHistory
    extra = 0
    can_delete = True
    max_num = 1
    fields = (
        ('disability', 'certified_disability', 'disability_percentage'),
        ('kepa_check', 'kepa_expiry'),
    )
    
    class Media:
        js = ('assets/js/conditional_fields.js',)

class ComorbidityInline(admin.StackedInline):
    model = Comorbidity
    extra = 0
    can_delete = True
    max_num = 1
    
    fieldsets = (
        ('Κύριες Παθήσεις', {
            'fields': (
                ('diabetes', 'arterial_disease'),
                ('cardiovascular_disease', 'copd'),
                ('psychiatric_disorder', 'nephropathy'),
            )
        }),
        ('Άλλες Παθήσεις', {
            'fields': (
                'mobility_issues',
                'other_conditions',
            ),
        }),
    )

class TherapyInline(admin.TabularInline):
    model = Therapy
    extra = 0
    fields = ("therapy_type", "hospital_name")  # Changed from therapy_type_id
    show_change_link = True
    
    # Use custom form if available
    if 'TherapyForm' in locals():  # Better way to check if TherapyForm exists
        form = TherapyForm

   
class ActionInline(admin.TabularInline):
    model = Action
    extra = 0
    fields = ('action_display', 'action_date', 'organization_display', 'result_summary', 'edit_link')
    readonly_fields = ('action_display', 'organization_display', 'result_summary', 'edit_link')
    can_delete = False
    show_change_link = False  # We'll use our custom edit_link instead
    
    def has_add_permission(self, request, obj=None):
        return False  # Disable adding from inline
    
    def action_display(self, obj):
        """Show action type and details"""
        return str(obj)
    action_display.short_description = "Ενέργεια"
    
    def organization_display(self, obj):
        """Show organization/contact"""
        return obj.organization_display or "-"
    organization_display.short_description = "Φορέας/Επαφή"
    
    def result_summary(self, obj):
        """Show truncated result"""
        if obj.result:
            return obj.result[:60] + "..." if len(obj.result) > 60 else obj.result
        return "-"
    result_summary.short_description = "Αποτέλεσμα"
    
    def edit_link(self, obj):
        """Link to edit action"""
        if obj.pk:
            url = reverse('admin:records_action_change', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">✏️ Επεξεργασία</a>', url)
        return "-"
    edit_link.short_description = "Ενέργειες"
        
class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ("document_type", "title", "file", "is_verified", "uploaded_by")
    readonly_fields = ("uploaded_by",)
    show_change_link = True
    
    def get_queryset(self, request):
        """Filter to show only relevant document types for medical context"""
        qs = super().get_queryset(request)
        # You might want to filter by document types relevant to medical history
        # For example, if you have DocumentType objects for medical documents:
        # medical_doc_types = DocumentType.objects.filter(
        #     name__in=['Πιστοποιητικό ΚΕΠΑ', 'Πιστοποιητικό Αναπηρίας', 'Ιατρική Γνωμάτευση']
        # )
        # return qs.filter(document_type__in=medical_doc_types)
        return qs

# ========== MAIN ADMIN CLASSES ==========
# Updated PersonAdminForm
class PersonAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Auto-increment registration number for new instances
        if not self.instance.pk:
            last_person = Person.objects.aggregate(
                max_reg=models.Max('registration_number')
            )['max_reg']
            #self.fields['registration_number'].initial = (last_person or 0) + 1
            self.instance.registration_number = (last_person or 0) + 1
        
        # Set up center field properly
        self.fields['center'].queryset = Center.objects.filter(is_active=True)
        
        # Organize field help texts
        self.fields['birth_year'].help_text = "Εισάγετε το έτος γέννησης (π.χ. 1980)"
        self.fields['amka'].help_text = "11-ψήφιο ΑΜΚΑ"
        self.fields['vat'].help_text = "9-ψήφιο ΑΦΜ"
        self.fields['id_card'].help_text = "8-ψήφιο αριθμό ταυτότητας"
        
    class Media:
        js = ('assets/js/conditional_fields.js', 'assets/js/cascading_dropdowns.js')
        
    class Meta:
        model = Person
        fields = '__all__'

def request_management(self, obj):
    """Enhanced request management interface"""
    if not obj.pk:
        return format_html('<em>Αποθηκεύστε πρώτα τον ωφελούμενο για να προσθέσετε αιτήματα</em>')
    
    try:
        requests = obj.requests.select_related(
            'status', 'category', 'assigned_to'
        ).prefetch_related('tags', 'actions').order_by('-created_at')
    except AttributeError:
        requests = Request.objects.filter(person=obj).select_related(
            'status', 'category', 'assigned_to'
        ).prefetch_related('tags', 'actions').order_by('-created_at')
    
    if not requests.exists():
        # No requests - show add button
        add_url = reverse('admin:records_request_add') + f'?person={obj.id}'
        return format_html(
            '<div style="text-align: center; padding: 20px; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px;">'
            '<p style="color: #6c757d; margin-bottom: 15px;"><em>Δεν υπάρχουν αιτήματα</em></p>'
            '<a href="{}" target="_blank" '
            'style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; '
            'text-decoration: none; border-radius: 6px; font-weight: bold;">'
            '➕ Προσθήκη πρώτου αιτήματος</a>'
            '</div>', add_url
        )
    
    # Group requests by status
    from collections import defaultdict
    status_groups = defaultdict(list)
    
    for request in requests:
        status_name = request.status.name if request.status else "Χωρίς κατάσταση"
        status_groups[status_name].append(request)
    
    # Build the display
    status_sections = []
    
    for status_name, status_requests in status_groups.items():
        count = len(status_requests)
        
        # Determine status color
        status_colors = {
            'Νέο': '#007bff',
            'Σε εξέλιξη': '#ffc107', 
            'Αναμονή': '#fd7e14',
            'Ολοκληρωμένο': '#28a745',
            'Ακυρώθηκε': '#dc3545',
            'Κλειστό': '#6c757d'
        }
        status_color = status_colors.get(status_name, '#6c757d')
        
        # Status header with count
        header = format_html(
            '<div style="background: {}; color: white; padding: 8px 12px; margin: 8px 0 4px 0; '
            'border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">'
            '<strong>{}</strong>'
            '<span style="background: rgba(255,255,255,0.3); padding: 2px 8px; border-radius: 12px; font-size: 12px;">{}</span>'
            '</div>',
            status_color, status_name, count
        )
        
        # Individual requests in this status
        request_cards = []
        for request in status_requests:
            # Priority indicator
            priority_colors = {1: '#dc3545', 2: '#ffc107', 3: '#28a745'}
            priority_color = priority_colors.get(request.priority, '#6c757d')
            priority_name = dict(request.PRIORITY_CHOICES).get(request.priority, 'Μέτρια')
            
            # Tags display
            tags = list(request.tags.all()[:3])
            tags_display = ", ".join([tag.name for tag in tags])
            if request.tags.count() > 3:
                tags_display += f" (+{request.tags.count() - 3})"
            if not tags_display:
                tags_display = "Χωρίς ετικέτες"
            
            # Category
            category_display = request.category.name if request.category else "Χωρίς κατηγορία"
            
            # Dates info
            date_info = []
            if request.submission_date:
                date_info.append(f"📅 Υποβλήθηκε: {request.submission_date.strftime('%d/%m/%Y')}")
            if request.due_date:
                due_color = '#dc3545' if request.is_overdue else '#28a745'
                date_info.append(f'<span style="color: {due_color};">⏰ Προθεσμία: {request.due_date.strftime("%d/%m/%Y")}</span>')
            
            date_html = '<br><small>' + ' • '.join(date_info) + '</small>' if date_info else ''
            
            # Assignment info
            assignment_info = ""
            if request.assigned_to:
                assignment_info = f'<br><small style="color: #17a2b8;">👤 Ανατέθηκε σε: {request.assigned_to.get_full_name() or request.assigned_to.username}</small>'
            
            # Actions count
            actions_count = request.actions.count() if hasattr(request, 'actions') else 0
            actions_info = ""
            if actions_count > 0:
                actions_info = f'<br><small style="color: #6f42c1;">⚡ {actions_count} ενέργειες</small>'
            
            # Days open indicator
            days_open = request.days_open
            days_color = '#dc3545' if days_open > 30 else '#ffc107' if days_open > 14 else '#28a745'
            
            # Edit link
            edit_url = reverse('admin:records_request_change', args=[request.id])
            
            # Card
            card = format_html(
                '<div style="margin: 4px 0; padding: 10px; background: white; border: 1px solid #e9ecef; border-radius: 4px;">'
                '<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
                '<div style="flex: 1;">'
                '<div style="display: flex; align-items: center; margin-bottom: 4px;">'
                '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-right: 8px;">{}</span>'
                '<span style="font-weight: bold; color: #495057;">{}</span>'
                '</div>'
                '<div style="font-size: 13px; color: #6c757d; margin-bottom: 4px;">🏷️ {}</div>'
                '<div style="font-size: 12px; color: #6c757d;">📂 {}</div>'
                '<div style="margin-top: 4px;">'
                '<span style="background: {}; color: white; padding: 1px 4px; border-radius: 2px; font-size: 10px;">{} ημέρες ανοικτό</span>'
                '</div>'
                '{}'
                '{}'
                '{}'
                '</div>'
                '<a href="{}" target="_blank" '
                'style="padding: 6px 10px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; margin-left: 10px;">'
                '✏️ Επεξεργασία</a>'
                '</div>'
                '</div>',
                priority_color, priority_name,
                category_display,
                tags_display,
                category_display,
                days_color, days_open,
                date_html,
                assignment_info,
                actions_info,
                edit_url
            )
            request_cards.append(card)
        
        # Combine header and cards
        status_section = header + ''.join(request_cards)
        status_sections.append(status_section)
    
    # Add new request button
    add_url = reverse('admin:records_request_add') + f'?person={obj.id}'
    add_button = format_html(
        '<div style="margin: 15px 0; text-align: center;">'
        '<a href="{}" target="_blank" '
        'style="display: inline-block; padding: 8px 16px; background: #007bff; color: white; '
        'text-decoration: none; border-radius: 4px; font-weight: bold;">'
        '➕ Προσθήκη νέου αιτήματος</a>'
        '</div>', add_url
    )
    
    # Summary at the top
    total_requests = requests.count()
    status_count = len(status_groups)
    
    # Calculate some stats
    open_requests = requests.exclude(status__is_closed=True).count() if hasattr(requests.first().status, 'is_closed') else 0
    overdue_requests = sum(1 for r in requests if r.is_overdue)
    
    summary = format_html(
        '<div style="background: #e3f2fd; padding: 10px; margin-bottom: 10px; border-radius: 4px; text-align: center;">'
        '<strong>Σύνοψη:</strong> {} αιτήματα συνολικά • {} ανοικτά • {} εκπρόθεσμα • {} καταστάσεις'
        '</div>',
        total_requests, open_requests, overdue_requests, status_count
    )
    
    return format_html(summary + ''.join(status_sections) + add_button)

def export_persons_csv(modeladmin, request, queryset):
    """Export selected persons to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="persons_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Registration Number', 'Last Name', 'First Name', 'AMKA', 'Center',
        'Gender', 'Age', 'Municipality', 'Mobile', 'Email', 'Insurance Status',
        'Marital Status', 'Created At'
    ])
    
    # Write data rows
    for person in queryset:
        writer.writerow([
            person.registration_number,
            person.last_name,
            person.first_name,
            person.amka,
            person.center.name if person.center else '',
            person.get_gender_display(),
            person.calculated_age,
            person.municipality.name if person.municipality else '',
            person.mobile,
            person.email,
            person.get_insurance_status_display(),
            person.get_marital_status_display(),
            person.created_at.strftime('%Y-%m-%d %H:%M:%S') if person.created_at else '',
        ])
    
    return response

export_persons_csv.short_description = "Export selected persons to CSV"
    
@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm
    actions = [export_persons_csv]  # Add this line

    list_display = (
        'full_name', 'center', 'age_display', 'gender', 
        'municipality_display', 'mobile', 'insurance_status',
        'neoplasm_count', 'request_count'
    )
    
    list_filter = (
        'gender', 'center', 'marital_status', 'insurance_status', 'status',
        'municipality__regional_unit__region', 'created_at'
    )
    
    search_fields = ('last_name', 'first_name', 'amka', 'mobile', 'email')
    
    readonly_fields = (
        'created_at', 'updated_at', 'calculated_age', 'bmi', 'bmi_category',
        'neoplasm_management', 'request_management', 'registration_number'
    )
    
    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': (
                ('last_name', 'first_name'),
                ('father_name', 'mother_name'),
                ('birth_year', 'calculated_age'),
                ('gender', 'marital_status'),
                ('children_count', 'minors', 'students', 'no_military_service'),
            )
        }),
        ('Ταυτότητα & Υπηκοότητα', {
            'fields': (
                ('nationality', 'citizenship'),
                ('vat', 'amka'),
                'id_card',
            )
        }),
        ('Επικοινωνία & Διεύθυνση', {
            'fields': (
                ('mobile', 'landline'),
                'email',
                'address',
                ('city', 'postal_code'),
                ('region', 'regional_unit', 'municipality'),
            )
        }),
        ('Ασφάλιση & Συντάξεις', {
            'fields': (
                ('insurance_status', 'insurance_provider'),
                'special_funds',
                ('widow_pension', 'disability_pension'),
            )
        }),
        ('Εργασιακά Στοιχεία', {
            'fields': (
                'status',
                # Unemployment fields (shown conditionally)
                ('unemployment_card', 'unemployment_registration_date'),
                # Employment fields (shown conditionally)
                ('profession', 'specialization'),
                ('employment_type', 'employer_name'),
                ('employer_legal_form', 'hire_date'),
                ('work_schedule', 'contract_type'),
            ),
        }),
        ('Φυσικά Χαρακτηριστικά', {
            'fields': (
                ('weight', 'height'),
                ('bmi', 'bmi_category'),
            ),
        }),
        ('Διαχειριστικά', {
            'fields': (
                ('registration_number', 'center'),
                'knowledge_source',
                ('created_at', 'updated_at'),
            )
        }),
        ('Νεοπλάσματα', {
            'fields': ('neoplasm_management',),
            'description': 'Διαχείριση νεοπλασμάτων του ωφελούμενου'
        }),
        ('Αιτήματα', {
            'fields': ('request_management',),
            'description': 'Διαχείριση αιτημάτων του ωφελούμενου'
        }),
    )
    
    # Remove RequestInline from inlines - now it's handled by request_management
    inlines = [
        ContactPersonInline,
        MedicalHistoryInline,
        ComorbidityInline,
        DocumentInline
    ]
    
    class Media:
        js = ('assets/js/conditional_fields.js', 'assets/js/cascading_dropdowns.js')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get_regional_units/', self.get_regional_units, name='get_regional_units'),
            path('get_municipalities/', self.get_municipalities, name='get_municipalities'),
        ]
        return custom_urls + urls
    
    def get_regional_units(self, request):
        region_id = request.GET.get('region_id')
        if region_id:
            units = RegionalUnit.objects.filter(region_id=region_id).order_by('sort_order', 'name')
            data = [{'id': unit.id, 'name': unit.name} for unit in units]
        else:
            data = []
        return JsonResponse(data, safe=False)
    
    def get_municipalities(self, request):
        unit_id = request.GET.get('unit_id')
        if unit_id:
            municipalities = Municipality.objects.filter(regional_unit_id=unit_id).order_by('sort_order', 'name')
            data = [{'id': muni.id, 'name': muni.name} for muni in municipalities]
        else:
            data = []
        return JsonResponse(data, safe=False)
    
    def full_name(self, obj):
        return f"{obj.last_name} {obj.first_name}"
    full_name.short_description = "Ονοματεπώνυμο"
    
    def age_display(self, obj):
        return obj.calculated_age if obj.calculated_age else "N/A"
    age_display.short_description = "Ηλικία"
    
    def municipality_display(self, obj):
        if obj.municipality:
            return f"{obj.municipality.name}, {obj.municipality.regional_unit.region.name}"
        return "-"
    municipality_display.short_description = "Περιοχή"
    
    def neoplasm_count(self, obj):
        try:
            neoplasms = obj.neoplasms.all()
        except AttributeError:
            neoplasms = Neoplasm.objects.filter(person=obj)
        
        count = neoplasms.count()
        if count > 0:
            url = reverse('admin:records_neoplasm_changelist') + f'?person__id__exact={obj.id}'
            return format_html(
                '<a href="{}" style="color: #417690; font-weight: bold;">'
                '📋 {} νεοπλάσματα</a>', 
                url, count
            )
        else:
            add_url = reverse('admin:records_neoplasm_add') + f'?person={obj.id}'
            return format_html(
                '<a href="{}" style="color: #28a745; font-weight: bold;">'
                '➕ Προσθήκη</a>', 
                add_url
            )
    neoplasm_count.short_description = "Νεοπλάσματα"
    
    def request_count(self, obj):
        try:
            requests = obj.requests.all()
        except AttributeError:
            requests = Request.objects.filter(person=obj)
        
        count = requests.count()
        if count > 0:
            # Get status breakdown for tooltip
            from collections import defaultdict
            statuses = defaultdict(int)
            for request in requests:
                status_name = request.status.name if request.status else "Χωρίς κατάσταση"
                statuses[status_name] += 1
            
            breakdown = ", ".join([f"{status}: {count}" for status, count in statuses.items()])
            url = reverse('admin:records_request_changelist') + f'?person__id__exact={obj.id}'
            
            return format_html(
                '<a href="{}" style="color: #007bff; font-weight: bold;" title="{}">'
                '📋 {} αιτήματα</a>', 
                url, breakdown, count
            )
        else:
            add_url = reverse('admin:records_request_add') + f'?person={obj.id}'
            return format_html(
                '<a href="{}" style="color: #007bff; font-weight: bold;">'
                '➕ Προσθήκη</a>', 
                add_url
            )
    request_count.short_description = "Αιτήματα"
    
    def neoplasm_management(self, obj):
        """Enhanced neoplasm management interface"""
        if not obj.pk:
            return format_html('<em>Αποθηκεύστε πρώτα τον ωφελούμενο για να προσθέσετε νεοπλάσματα</em>')
        
        try:
            neoplasms = obj.neoplasms.select_related(
                'icd10_category', 'icd10_subcategory', 'icd10_code'
            ).prefetch_related('therapies').order_by('-created_at')
        except AttributeError:
            from .models import Neoplasm  # Make sure to import
            neoplasms = Neoplasm.objects.filter(person=obj).select_related(
                'icd10_category', 'icd10_subcategory', 'icd10_code'
            ).prefetch_related('therapies').order_by('-created_at')
        
        if not neoplasms.exists():
            # No neoplasms - show add button
            add_url = reverse('admin:records_neoplasm_add') + f'?person={obj.id}'
            return format_html(
                '<div style="text-align: center; padding: 20px; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 8px;">'
                '<p style="color: #6c757d; margin-bottom: 15px;"><em>Δεν υπάρχουν νεοπλάσματα</em></p>'
                '<a href="{}" target="_blank" '
                'style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; '
                'text-decoration: none; border-radius: 6px; font-weight: bold;">'
                '➕ Προσθήκη πρώτου νεοπλάσματος</a>'
                '</div>', add_url
            )
        
        # Build comprehensive display
        neoplasm_cards = []
        
        for neoplasm in neoplasms:
            # Basic info
            category_name = neoplasm.icd10_category.name if neoplasm.icd10_category else "Χωρίς κατηγορία"
            code_info = f"{neoplasm.icd10_code.code}" if neoplasm.icd10_code else "Χωρίς κωδικό"
            code_label = f"- {neoplasm.icd10_code.label}" if neoplasm.icd10_code else ""
            location_info = f"📍 {neoplasm.localization}" if neoplasm.localization else ""
            
            # Status indicators
            status_badges = []
            if neoplasm.metastasis:
                status_badges.append('<span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">🔴 Μεταστάσεις</span>')
            if neoplasm.surgery:
                surgery_info = f" στο {neoplasm.surgery_hospital}" if neoplasm.surgery_hospital else ""
                status_badges.append(f'<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">✅ Χειρουργείο{surgery_info}</span>')
            if neoplasm.scheduled_surgery:
                status_badges.append('<span style="background: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; font-size: 11px;">⏰ Προγραμματισμένο</span>')
            
            status_html = '<br>' + ' '.join(status_badges) if status_badges else ''
            
            # Therapies
            therapies = neoplasm.therapies.all()
            therapy_html = ""
            if therapies.exists():
                therapy_list = []
                for therapy in therapies:
                    therapy_name = therapy.get_therapy_type_display()
                    hospital = f" ({therapy.hospital_name})" if therapy.hospital_name else ""
                    therapy_list.append(f"💊 {therapy_name}{hospital}")
                therapy_html = '<br><small style="color: #17a2b8;">' + '<br>'.join(therapy_list) + '</small>'
            
            # Edit link
            edit_url = reverse('admin:records_neoplasm_change', args=[neoplasm.id])
            
            # Card
            card = format_html(
                '<div style="margin: 8px 0; padding: 12px; background: white; border-left: 4px solid #007bff; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
                '<div style="display: flex; justify-content: space-between; align-items: flex-start;">'
                '<div style="flex: 1;">'
                '<div style="font-weight: bold; color: #007bff; margin-bottom: 4px;">{}</div>'
                '<div style="font-size: 14px; color: #495057;">{} {}</div>'
                '<div style="font-size: 12px; color: #6c757d; margin-top: 2px;">{}</div>'
                '{}'
                '{}'
                '</div>'
                '<a href="{}" target="_blank" '
                'style="padding: 6px 12px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; font-size: 12px; margin-left: 10px;">'
                '✏️ Επεξεργασία</a>'
                '</div>'
                '</div>',
                category_name,
                code_info, code_label,
                location_info,
                status_html,
                therapy_html,
                edit_url
            )
            neoplasm_cards.append(card)
        
        # Add new button and summary
        add_url = reverse('admin:records_neoplasm_add') + f'?person={obj.id}'
        add_button = format_html(
            '<div style="margin: 15px 0; text-align: center;">'
            '<a href="{}" target="_blank" '
            'style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; '
            'text-decoration: none; border-radius: 4px; font-weight: bold;">'
            '➕ Προσθήκη νέου νεοπλάσματος</a>'
            '</div>', add_url
        )
        
        # Summary
        total_count = neoplasms.count()
        total_therapies = sum(n.therapies.count() for n in neoplasms)
        summary = format_html(
            '<div style="background: #e3f2fd; padding: 10px; margin-bottom: 10px; border-radius: 4px; text-align: center;">'
            '<strong>Σύνοψη:</strong> {} νεοπλάσματα με {} θεραπείες συνολικά'
            '</div>',
            total_count, total_therapies
        )
        
        return format_html(summary + ''.join(neoplasm_cards) + add_button)

    neoplasm_management.short_description = "Διαχείριση νεοπλασμάτων"

    # Include the request_management method here
    request_management = request_management



@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('person_name', 'status', 'priority_display', 'submission_date', 'tags_display', 'assigned_to', 'days_open_display')
    list_filter = ('status', 'category', 'priority', 'communication_method', 'assigned_to', 'created_at')
    search_fields = ('person__last_name', 'person__first_name', 'subject', 'description')
    readonly_fields = ('created_at', 'updated_at', 'days_open', 'number_of_actions', 'update_date', 'actions_management')
    
    filter_horizontal = ('tags',)
    inlines = [DocumentInline]
    
    # Use custom form if available
    if RequestForm:
        form = RequestForm
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': (
                'person',
                'category',
                'status',
                'priority',
            )
        }),
        ('Επικοινωνία', {
            'fields': (
                ('contact_person_type', 'communication_method','subject',),
                ('submission_date', 'update_date'),
            )
        }),
        ('Περιεχόμενο', {
            'fields': (
                'tags',
            )
        }),
        ('Διαχείριση', {
            'fields': (
                ('created_by','assigned_to'),
                ('due_date', 'closed_date'),
                ('protocol_number', 'is_accepted'),
                ('days_open', 'number_of_actions'),
                'actions_management',
            )
        }),
        ('Timestamps', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',)
        }),
    )
    
    def person_name(self, obj):
        return str(obj.person)
    person_name.short_description = "Ωφελούμενος"
    
    def actions_management(self, obj):
        """Management buttons for actions"""
        if not obj.pk:
            return "Αποθηκεύστε πρώτα το αίτημα για να διαχειριστείτε ενέργειες"
        
        actions_count = obj.actions.count()
        
        # Add new action button
        add_url = reverse('admin:records_action_add') + f'?request={obj.pk}'
        add_button = f'<a href="{add_url}" style="background: #28a745; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; margin-right: 10px;">➕ Νέα Ενέργεια</a>'
        
        # View all actions button
        list_url = reverse('admin:records_action_changelist') + f'?request__id__exact={obj.pk}'
        view_button = f'<a href="{list_url}" style="background: #007bff; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px;">📋 Προβολή Ενεργειών ({actions_count})</a>'
        
        return format_html(add_button + view_button)
    
    actions_management.short_description = "Διαχείριση Ενεργειών"
    
    def tags_display(self, obj):
        tags = list(obj.tags.all()[:3])  # Show first 3 tags
        if not tags:
            return "-"
        
        display = ", ".join([tag.name for tag in tags])
        if obj.tags.count() > 3:
            display += f" (+{obj.tags.count() - 3})"
        return display
    tags_display.short_description = "Ετικέτες"
    
    def priority_display(self, obj):
        colors = {1: 'red', 2: 'orange', 3: 'green'}
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_display.short_description = "Προτεραιότητα"
    
    def days_open_display(self, obj):
        days = obj.days_open
        if days > 30:
            color = 'red'
        elif days > 14:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{} ημέρες</span>', color, days)
    days_open_display.short_description = "Ημέρες Ανοικτό"


@admin.register(Neoplasm)
class NeoplasmAdmin(admin.ModelAdmin):
    list_display = ("person", "icd10_code", "localization", "metastasis", "surgery", "therapy_count")
    list_filter = ('icd10_category', "metastasis", "surgery", )
    search_fields = ("person__last_name", "person__first_name", "icd10_code__code", "localization")
    inlines = [TherapyInline]
    
    # Use custom form if available
    if NeoplasmForm:
        form = NeoplasmForm
        
    class Media:
        js = ('assets/js/neoplasm_cascading.js',)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('get_subcategories/', self.get_subcategories, name='get_neoplasm_subcategories'),
            path('get_codes/', self.get_codes, name='get_neoplasm_codes'),
        ]
        return custom_urls + urls
    
    def get_subcategories(self, request):
        category_id = request.GET.get('category_id')
        if category_id:
            subcategories = ICD10Subcategory.objects.filter(category_id=category_id).order_by('sort_order', 'name')
            data = [{'id': sub.id, 'name': sub.name} for sub in subcategories]
        else:
            data = []
        return JsonResponse(data, safe=False)
    
    def get_codes(self, request):
        subcategory_id = request.GET.get('subcategory_id')
        if subcategory_id:
            codes = ICD10Code.objects.filter(subcategory_id=subcategory_id).order_by('code')
            data = [{'id': code.id, 'name': f"{code.code} - {code.label}"} for code in codes]
        else:
            data = []
        return JsonResponse(data, safe=False)
    
    def icd10_code_display(self, obj):
        if obj.icd10_code:
            return f"{obj.icd10_code.code} - {obj.icd10_code.label}"
        return "-"
    icd10_code_display.short_description = "ICD10 Κωδικός"
    
    def therapy_count(self, obj):
        """Display therapy count for this neoplasm"""
        try:
            therapies = obj.therapies.all()
            count = therapies.count()
            
            if count > 0:
                # Group therapies by type for tooltip
                therapy_types = {}
                for therapy in therapies:
                    therapy_type = therapy.get_therapy_type_display() if therapy.therapy_type else "Άλλο"
                    therapy_types[therapy_type] = therapy_types.get(therapy_type, 0) + 1
                
                breakdown = ", ".join([f"{ttype}: {count}" for ttype, count in therapy_types.items()])
                
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;" title="{}">'
                    '💊 {} θεραπείες</span>', 
                    breakdown, count
                )
            else:
                return format_html(
                    '<span style="color: #6c757d;">—</span>'
                )
        except AttributeError:
            return "—"
    
    therapy_count.short_description = "Θεραπείες"
      
    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': ('person',)
        }),
        ('Κατηγοριοποίηση ICD10', {
            'fields': ('icd10_category', 'icd10_subcategory', 'icd10_code')
        }),
        ('Λεπτομέρειες', {
            'fields': ('localization', 'metastasis')
        }),
        ('Χειρουργείο', {
            'fields': ('surgery', 'surgery_hospital', 'scheduled_surgery')
        }),
    )

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        
        # Pre-populate person field if coming from person admin
        if 'person' in request.GET:
            try:
                person_id = request.GET['person']
                person = Person.objects.get(id=person_id)
                extra_context['person_name'] = f"Προσθήκη νεοπλάσματος για: {person}"
            except:
                pass
                
        return super().add_view(request, form_url, extra_context)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Pre-populate person field when adding
        if 'person' in request.GET and not obj:
            try:
                person_id = request.GET['person']
                form.base_fields['person'].initial = person_id
                # Make the field readonly when pre-populated
                form.base_fields['person'].widget.attrs['readonly'] = True
            except:
                pass
        
        return form    
    
    
    

class KEPAExpiryFilter(admin.SimpleListFilter):
    title = 'Κατάσταση Λήξης ΚΕΠΑ'
    parameter_name = 'kepa_expiry_status'
    
    def lookups(self, request, model_admin):
        return (
            ('expired', '🚨 Έχει λήξει'),
            ('critical', '🔴 Επείγον (≤4 μήνες)'),
            ('warning', '🟡 Προσοχή (≤6 μήνες)'),
            ('ok', '✅ Εντάξει (>6 μήνες)'),
            ('no_date', '⚠️ Χωρίς ημερομηνία'),
        )
    
    def queryset(self, request, queryset):
        today = timezone.now().date()
        
        if self.value() == 'expired':
            return queryset.filter(
                kepa_check=True,
                kepa_expiry__lt=today
            )
        elif self.value() == 'critical':
            critical_date = today + timedelta(days=120)
            return queryset.filter(
                kepa_check=True,
                kepa_expiry__gte=today,
                kepa_expiry__lte=critical_date
            )
        elif self.value() == 'warning':
            warning_date = today + timedelta(days=180)
            critical_date = today + timedelta(days=120)
            return queryset.filter(
                kepa_check=True,
                kepa_expiry__gt=critical_date,
                kepa_expiry__lte=warning_date
            )
        elif self.value() == 'ok':
            ok_date = today + timedelta(days=180)
            return queryset.filter(
                kepa_check=True,
                kepa_expiry__gt=ok_date
            )
        elif self.value() == 'no_date':
            return queryset.filter(
                kepa_check=True,
                kepa_expiry__isnull=True
            )

# Also add this action to export KEPA expiring records
def export_kepa_expiring_csv(modeladmin, request, queryset):
    """Export KEPA records expiring soon"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="kepa_expiring_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')  # UTF-8 BOM for Excel
    
    writer = csv.writer(response)
    writer.writerow([
        'Επώνυμο', 'Όνομα', 'Τηλέφωνο', 'Email', 'Κέντρο',
        'Ημερομηνία Λήξης ΚΕΠΑ', 'Μήνες Μέχρι Λήξη (περίπου)', 'Κατάσταση'
    ])
    
    today = timezone.now().date()
    
    for medical_history in queryset.filter(kepa_check=True, kepa_expiry__isnull=False):
        person = medical_history.person
        days_until_expiry = (medical_history.kepa_expiry - today).days
        months_until_expiry = round(days_until_expiry / 30.44)  # Whole months
        
        if days_until_expiry < 0:
            status = "ΕΧΕΙ ΛΗΞΕΙ"
            months_display = f"~{abs(months_until_expiry)} (έχει λήξει)"
        elif days_until_expiry <= 120:
            status = "ΕΠΕΙΓΟΝ"
            months_display = f"~{months_until_expiry}"
        elif days_until_expiry <= 180:
            status = "ΠΡΟΣΟΧΗ"
            months_display = f"~{months_until_expiry}"
        else:
            status = "ΕΝΤAΞΕΙ"
            months_display = f"~{months_until_expiry}"
        
        writer.writerow([
            person.last_name,
            person.first_name,
            person.mobile,
            person.email,
            person.center.name if person.center else '',
            medical_history.kepa_expiry.strftime('%d/%m/%Y'),
            months_display,
            status
        ])
    
    return response

export_kepa_expiring_csv.short_description = "Εξαγωγή ΚΕΠΑ που λήγουν (CSV)"

@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ("person", "disability", "certified_disability", "disability_percentage", "kepa_check", "kepa_expiry_alert")
    list_filter = ("disability", "certified_disability", "kepa_check", KEPAExpiryFilter)
    search_fields = ("person__last_name", "person__first_name")
    actions = [export_kepa_expiring_csv]  # Add this line
    
    readonly_fields = ('comorbidities_detail','documents_detail')
    
    # Add the conditional fields JavaScript
    class Media:
        js = ('assets/js/conditional_fields.js',)
    
    def documents_detail(self, obj):
        """Display documents related to this person"""
        if not obj.person:
            return "Δεν υπάρχει ωφελούμενος"
            
        documents = obj.person.documents.all().order_by('-created_at')
        
        if not documents.exists():
            # No documents - show add button
            add_url = reverse('admin:records_document_add') + f'?person={obj.person.id}'
            return format_html(
                '<div style="text-align: center; padding: 15px; background: #f8f9fa; border: 2px dashed #dee2e6; border-radius: 6px;">'
                '<p style="color: #6c757d; margin-bottom: 10px;"><em>Δεν υπάρχουν έγγραφα</em></p>'
                '<a href="{}" target="_blank" '
                'style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; '
                'text-decoration: none; border-radius: 4px; font-weight: bold;">'
                '📄 Προσθήκη εγγράφου</a>'
                '</div>', add_url
            )
        
        # Group documents by type
        from collections import defaultdict
        doc_groups = defaultdict(list)
        
        for doc in documents:
            doc_type = doc.document_type.name if doc.document_type else "Χωρίς κατηγορία"
            doc_groups[doc_type].append(doc)
        
        # Build the display
        group_sections = []
        
        for doc_type, type_docs in doc_groups.items():
            count = len(type_docs)
            
            # Group header
            header = (
                f'<div style="background: #e8f4fd; padding: 6px 10px; margin: 6px 0 2px 0; '
                f'border-left: 3px solid #007bff; border-radius: 3px;">'
                f'<strong style="color: #007bff;">{doc_type}</strong> '
                f'<span style="background: #007bff; color: white; padding: 1px 6px; '
                f'border-radius: 10px; font-size: 11px; margin-left: 6px;">{count}</span>'
                f'</div>'
            )
            
            # Individual documents
            doc_items = []
            for doc in type_docs:
                edit_url = reverse('admin:records_document_change', args=[doc.id])
                
                # Document info
                title = doc.title or doc.original_filename or f"Έγγραφο {doc.id}"
                
                # File size
                file_size = ""
                if doc.file_size:
                    if doc.file_size < 1024*1024:
                        file_size = f"({doc.file_size/1024:.0f} KB)"
                    else:
                        file_size = f"({doc.file_size/(1024*1024):.1f} MB)"
                
                # Verification status
                verified_status = ""
                if doc.is_verified:
                    verified_status = '<span style="color: #28a745; font-size: 11px;">✅ Επαληθευμένο</span>'
                else:
                    verified_status = '<span style="color: #ffc107; font-size: 11px;">⏳ Μη επαληθευμένο</span>'
                
                doc_item = (
                    f'<div style="margin: 2px 0; padding: 6px; background: white; '
                    f'border: 1px solid #e9ecef; border-radius: 3px; font-size: 12px;">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                    f'<div>'
                    f'<strong>{title}</strong> {file_size}<br>'
                    f'<small style="color: #6c757d;">{doc.created_at.strftime("%d/%m/%Y")}</small> • {verified_status}'
                    f'</div>'
                    f'<a href="{edit_url}" target="_blank" '
                    f'style="padding: 3px 6px; background: #007bff; color: white; '
                    f'text-decoration: none; border-radius: 3px; font-size: 10px;">✏️</a>'
                    f'</div>'
                    f'</div>'
                )
                doc_items.append(doc_item)
            
            # Combine header and items
            group_section = header + ''.join(doc_items)
            group_sections.append(group_section)
        
        # Add "Add new" button
        add_url = reverse('admin:records_document_add') + f'?person={obj.person.id}'
        add_button = (
            f'<div style="margin: 10px 0; text-align: center;">'
            f'<a href="{add_url}" target="_blank" '
            f'style="display: inline-block; padding: 6px 12px; background: #28a745; color: white; '
            f'text-decoration: none; border-radius: 3px; font-size: 12px;">'
            f'📄 Προσθήκη νέου εγγράφου</a>'
            f'</div>'
        )
        
        # Summary at the top
        total_count = documents.count()
        type_count = len(doc_groups)
        summary = (
            f'<div style="background: #fff3cd; padding: 8px; margin-bottom: 8px; '
            f'border-left: 3px solid #ffc107; border-radius: 3px; font-size: 12px;">'
            f'<strong>Σύνοψη:</strong> {total_count} έγγραφα σε {type_count} κατηγορί{"ες" if type_count != 1 else "α"}'
            f'</div>'
        )
        
        return format_html(summary + ''.join(group_sections) + add_button)

    documents_detail.short_description = "Έγγραφα"
    def comorbidities_detail(self, obj):
        """Display detailed comorbidities in the form"""
        if not obj.person:
            return "Δεν υπάρχει ωφελούμενος"
            
        try:
            comorbidity = obj.person.comorbidity
            
            # Build a detailed view
            conditions = []
            if comorbidity.diabetes:
                conditions.append("✅ Διαβήτης")
            if comorbidity.arterial_disease:
                conditions.append("✅ Αρτηριακή νόσος")
            if comorbidity.cardiovascular_disease:
                conditions.append("✅ Καρδιαγγειακή νόσος")
            if comorbidity.copd:
                conditions.append("✅ ΧΑΠ")
            if comorbidity.psychiatric_disorder:
                conditions.append("✅ Ψυχιατρική διαταραχή")
            if comorbidity.nephropathy:
                conditions.append("✅ Νεφροπάθεια")
            if comorbidity.mobility_issues:
                conditions.append("✅ Προβλήματα κινητικότητας")
            
            if conditions:
                conditions_html = "<br>".join(conditions)
            else:
                conditions_html = '<span style="color: #28a745;">Χωρίς παθήσεις</span>'
            
            other_conditions = ""
            if comorbidity.other_conditions:
                other_conditions = f'<br><br><strong>Άλλες παθήσεις:</strong><br>{comorbidity.other_conditions}'
            
            # Add edit link
            edit_url = reverse('admin:records_comorbidity_change', args=[comorbidity.id])
            edit_link = f'<br><br><a href="{edit_url}" target="_blank" style="color: #007bff;">✏️ Επεξεργασία συννοσηροτήτων</a>'
            
            return format_html(conditions_html + other_conditions + edit_link)
            
        except Comorbidity.DoesNotExist:
            # Create link to add comorbidity
            add_url = reverse('admin:records_comorbidity_add') + f'?person={obj.person.id}'
            return format_html(
                '<span style="color: #6c757d;">Δεν έχουν οριστεί συννοσηρότητες</span><br>'
                '<a href="{}" target="_blank" style="color: #28a745;">➕ Προσθήκη συννοσηροτήτων</a>',
                add_url
            )
    
    comorbidities_detail.short_description = "Συννοσηρότητες"
    
    def comorbidities_summary(self, obj):
        """Display summary of comorbidities"""
        try:
            comorbidity = obj.person.comorbidity
            conditions = []
            
            # Check each condition
            if comorbidity.diabetes:
                conditions.append("Διαβήτης")
            if comorbidity.arterial_disease:
                conditions.append("Αρτηριακή νόσος")
            if comorbidity.cardiovascular_disease:
                conditions.append("Καρδιαγγειακή νόσος")
            if comorbidity.copd:
                conditions.append("ΧΑΠ")
            if comorbidity.psychiatric_disorder:
                conditions.append("Ψυχιατρική διαταραχή")
            if comorbidity.nephropathy:
                conditions.append("Νεφροπάθεια")
            if comorbidity.mobility_issues:
                conditions.append("Προβλήματα κινητικότητας")
            if comorbidity.other_conditions:
                conditions.append("Άλλες παθήσεις")
            
            if conditions:
                summary = ", ".join(conditions[:3])  # Show first 3
                if len(conditions) > 3:
                    summary += f" (+{len(conditions) - 3})"
                
                return format_html(
                    '<span style="color: #dc3545;" title="{}">{}</span>',
                    ", ".join(conditions),  # Full list in tooltip
                    summary
                )
            else:
                return format_html('<span style="color: #28a745;">Χωρίς παθήσεις</span>')
                
        except Comorbidity.DoesNotExist:
            return format_html('<span style="color: #6c757d;">Δεν έχει οριστεί</span>')
    
    comorbidities_summary.short_description = "Συννοσηρότητες"
    
    def kepa_expiry_alert(self, obj):
        """Display KEPA expiry with color-coded alerts"""
        if not obj.kepa_expiry:
            if obj.kepa_check:
                return format_html(
                    '<span style="color: #dc3545; font-weight: bold;">⚠️ Δεν έχει οριστεί ημερομηνία λήξης</span>'
                )
            return "—"
        
        today = timezone.now().date()
        days_until_expiry = (obj.kepa_expiry - today).days
        
        # Convert days to months (approximately)
        months_until_expiry = round(days_until_expiry / 30.44)  # Round to whole months
        
        if days_until_expiry < 0:
            # Expired
            months_expired = abs(round(days_until_expiry / 30.44))
            return format_html(
                '<span style="color: #dc3545; font-weight: bold; background: #f8d7da; padding: 2px 6px; border-radius: 3px;">'
                '⚠️ ΕΧΕΙ ΛΗΞΕΙ (~{} μήνες πριν)</span>',
                months_expired
            )
        elif days_until_expiry <= 120:  # 4 months
            # Critical alert (4 months or less)
            return format_html(
                '<span style="color: #dc3545; font-weight: bold; background: #f8d7da; padding: 2px 6px; border-radius: 3px;">'
                'ΕΠΕΙΓΟΝ: ~{} μήνες (λήγει: {})</span>',
                months_until_expiry,
                obj.kepa_expiry.strftime('%d/%m/%Y')
            )
        elif days_until_expiry <= 180:  # 6 months
            # Warning alert (6 months or less)
            return format_html(
                '<span style="color: #856404; font-weight: bold; background: #fff3cd; padding: 2px 6px; border-radius: 3px;">'
                'ΠΡΟΣΟΧΗ: ~{} μήνες (λήγει: {})</span>',
                months_until_expiry,
                obj.kepa_expiry.strftime('%d/%m/%Y')
            )
        else:
            # OK
            return format_html(
                '<span style="color: #155724; background: #d4edda; padding: 2px 6px; border-radius: 3px;">'
                '✅ ~{} μήνες (λήγει: {})</span>',
                months_until_expiry,
                obj.kepa_expiry.strftime('%d/%m/%Y')
            )

    
    kepa_expiry_alert.short_description = "Λήξη ΚΕΠΑ"
    kepa_expiry_alert.admin_order_field = "kepa_expiry"
    
    # Optional: organize fields in fieldsets
    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': ('person',)
        }),
        ('Αναπηρία', {
            'fields': (
                'disability',
                'certified_disability', 
                'disability_percentage'
            )
        }),
        ('ΚΕΠΑ', {
            'fields': ('kepa_check', 'kepa_expiry'),
        }),
        ('Συννοσηρότητες', {
            'fields': ('comorbidities_detail',),
            'description': 'Οι συννοσηρότητες διαχειρίζονται ξεχωριστά αλλά εμφανίζονται εδώ για ευκολία.'
        }),
        ('Έγγραφα', {
            'fields': ('documents_detail',),
            'description': 'Πιστοποιητικά ΚΕΠΑ, αναπηρίας και άλλα σχετικά έγγραφα.'
        }),
        # Add other fieldsets as needed
    )

@admin.register(Comorbidity)
class ComorbidityAdmin(admin.ModelAdmin):
    list_display = ("person", "conditions_summary", "arterial_disease", "cardiovascular_disease", "copd", "diabetes", "psychiatric_disorder", "mobility_issues", "nephropathy")
    list_filter = ("diabetes", "arterial_disease", "cardiovascular_disease", "copd", "psychiatric_disorder", "mobility_issues", "nephropathy")
    search_fields = ("person__last_name", "person__first_name", "other_conditions")
    
    def conditions_summary(self, obj):
        """Show a quick summary of active conditions"""
        conditions = []
        if obj.diabetes: conditions.append("Διαβήτης")
        if obj.arterial_disease: conditions.append("Αρτηριακή")
        if obj.cardiovascular_disease: conditions.append("Καρδιαγγειακή")
        if obj.copd: conditions.append("ΧΑΠ")
        if obj.psychiatric_disorder: conditions.append("Ψυχιατρική")
        if obj.nephropathy: conditions.append("Νεφροπάθεια")
        if obj.mobility_issues: conditions.append("Κινητικά")
        
        if conditions:
            return f"{len(conditions)} παθήσεις: {', '.join(conditions[:2])}{'...' if len(conditions) > 2 else ''}"
        return "Χωρίς παθήσεις"
    
    conditions_summary.short_description = "Σύνοψη Παθήσεων"
    
    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': ('person',)
        }),
        ('Κύριες Παθήσεις', {
            'fields': (
                ('diabetes', 'arterial_disease'),
                ('cardiovascular_disease', 'copd'),
                ('psychiatric_disorder', 'nephropathy'),
                'mobility_issues',
            )
        }),
        ('Άλλες Παθήσεις', {
            'fields': ('other_conditions',),
        }),
    )
    
@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('request_link', 'action_display', 'action_date', 'org_name', 'is_completed')
    list_filter = ('action_type', 'direction', 'is_completed', 'action_date')
    search_fields = ('request__person__last_name', 'org_name', 'contact_name', 'result')
    date_hierarchy = 'action_date'

    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': ('request', 'person_display')
        }),
        ('Τύπος ενέργειας', {
            'fields': ('action_type', 'direction')
        }),
        ('Λεπτομέρειες', {
            'fields': ('action_date', 'performed_by')
        }),
        ('Επαφή', {
            'fields': ('org_name', 'contact_name', 'contact_role', 'contact_phone', 'contact_email'),
            'classes': ('collapse',)
        }),
        ('Αποτέλεσμα', {
            'fields': ('result', 'is_completed', 'follow_up_date')
        }),
    )
    readonly_fields = ('person_display',)

    def person_display(self, obj):
        if obj and obj.request and obj.request.person:
            return str(obj.request.person)
        return "-"
    person_display.short_description = "Ωφελούμενος"

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'request' in request.GET and not obj:
            try:
                request_id = request.GET['request']
                req = Request.objects.get(id=request_id)
                form.base_fields['request'].initial = request_id
                form.base_fields['request'].widget.attrs['readonly'] = True
            except Request.DoesNotExist:
                pass
        return form

    def save_model(self, request, obj, form, change):
        if obj.request and not obj.person_id:
            obj.person = obj.request.person
        super().save_model(request, obj, form, change)

    def action_display(self, obj):
        return str(obj)
    action_display.short_description = "Ενέργεια"

    def request_link(self, obj):
        url = reverse('admin:records_request_change', args=[obj.request.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.request))
    request_link.short_description = "Αίτημα"


# ========== LOOKUP ADMIN CLASSES ==========

@admin.register(RequestTag)
class RequestTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'estimated_duration_days', 'requires_documents', 'is_active')
    list_filter = ('category', 'requires_documents', 'requires_external_contact', 'is_active')
    search_fields = ('name', 'description')

@admin.register(RequestStatus)
class RequestStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "is_closed", "requires_action")
    list_filter = ("is_closed", "requires_action")
    search_fields = ("name",)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'unit_count')
    
    def unit_count(self, obj):
        return obj.regional_units.count()
    unit_count.short_description = "Περιφερειακές Ενότητες"


@admin.register(RegionalUnit)
class RegionalUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'municipality_count')
    list_filter = ('region',)
    
    def municipality_count(self, obj):
        return obj.municipalities.count()
    municipality_count.short_description = "Δήμοι"


@admin.register(Municipality)
class MunicipalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'regional_unit', 'region_name')
    list_filter = ('regional_unit__region', 'regional_unit')
    search_fields = ('name',)
    
    def region_name(self, obj):
        return obj.regional_unit.region.name
    region_name.short_description = "Περιφέρεια"


@admin.register(ICD10Code)
class ICD10CodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'category', 'is_common')
    list_filter = ('category', 'is_common', 'is_active')
    search_fields = ('code', 'label')


@admin.register(ICD10Category)
class ICD10CategoryAdmin(admin.ModelAdmin):
    list_display = ('code_range', 'name', 'is_cancer_related')
    list_filter = ('is_cancer_related',)
    search_fields = ('name', 'code_range')


@admin.register(ICD10Subcategory)
class ICD10SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'code_range_start', 'code_range_end')
    list_filter = ('category',)
    search_fields = ('name',)


# ========== SIMPLE REGISTRATIONS ==========

@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ['person', 'last_name', 'first_name', 'relation', 'mobile']
    list_filter = ['relation', 'is_primary']
    search_fields = ['last_name', 'first_name', 'person__last_name', 'person__first_name']

@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email']
    search_fields = ['name']

class ExpiryStatusFilter(admin.SimpleListFilter):
    title = 'Κατάσταση Λήξης'
    parameter_name = 'expiry_status'
    
    def lookups(self, request, model_admin):
        return (
            ('expired', '⚠️ Έχει λήξει'),
            ('expires_soon', '⏰ Λήγει σύντομα'),
            ('active', '✅ Ενεργό'),
            ('no_expiry', '➖ Χωρίς λήξη'),
        )
    
    def queryset(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        if self.value() == 'expired':
            return queryset.filter(expiry_date__lt=today)
        elif self.value() == 'expires_soon':
            # Documents expiring within 30 days
            soon = today + timedelta(days=30)
            return queryset.filter(expiry_date__gte=today, expiry_date__lte=soon)
        elif self.value() == 'active':
            soon = today + timedelta(days=30)
            return queryset.filter(expiry_date__gt=soon)
        elif self.value() == 'no_expiry':
            return queryset.filter(expiry_date__isnull=True)
            
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['person', 'document_type', 'title', 'is_verified', 'created_at']
    list_filter = ['document_type', 'is_verified', 'created_at']
    search_fields = ['person__last_name', 'person__first_name', 'title']

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_required_for_requests']
    list_filter = ['is_required_for_requests']
    search_fields = ['name', 'description']
    list_editable = ['is_required_for_requests']

#@admin.register(DocumentType)
#class DocumentTypeAdmin(admin.ModelAdmin):
#    list_display = ['name', 'is_required_for_requests']
#    list_filter = ['is_required_for_requests']
#    search_fields = ['name']

#@admin.register(TherapyType)
#class TherapyTypeAdmin(admin.ModelAdmin):
#    list_display = ["name", "therapy_category"]
#    list_filter = ["therapy_category"]
#    search_fields = ["name"]

# ========== ADMIN SITE CUSTOMIZATION ==========

admin.site.site_header = "K3 - Διαχείριση Ωφελούμενων"
admin.site.site_title = "K3 Admin"
admin.site.index_title = "Καλώς ήρθατε στο σύστημα K3"