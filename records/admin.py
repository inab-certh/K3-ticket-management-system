# records/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import JsonResponse
from django.urls import path
from django import forms
from django.db import models


# Import all models
from .models import (
    # Person related
    Person, ContactPerson,
    # Medical
    MedicalHistory, Neoplasm, Therapy, Comorbidity,
    # Requests
    Request, RequestTag, RequestAttachment,
    # Actions
    Action, ActionAttachment,
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

class MedicalHistoryInline(admin.StackedInline):
    model = MedicalHistory
    extra = 0
    can_delete = True
    max_num = 1

class ComorbidityInline(admin.StackedInline):
    model = Comorbidity
    extra = 0
    can_delete = True
    max_num = 1

class NeoplasmInline(admin.TabularInline):
    model = Neoplasm
    extra = 1
    show_change_link = True
    # Include all the cascading fields
    fields = ('icd10_category', 'icd10_subcategory', 'icd10_code', 'localization', 'metastasis', 'surgery')
    
    # Add the JavaScript
    class Media:
        js = ('assets/js/neoplasm_cascading.js',)

class TherapyInline(admin.TabularInline):
    model = Therapy
    extra = 0
    fields = ("therapy_type", "hospital_name", "start_date")
    show_change_link = True
    
    # Use custom form if available
    if TherapyForm:
        form = TherapyForm

class RequestInline(admin.TabularInline):
    model = Request
    extra = 0
    fields = ('primary_category', 'status', 'submission_date', 'assigned_to')
    readonly_fields = ('primary_category', 'submission_date')
    
class ActionInline(admin.TabularInline):
    model = Action
    extra = 1
    fields = ('action_type', 'action_date', 'external_org', 'result', 'is_completed')
    show_change_link = True

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0
    fields = ("document_type", "title", "uploaded_by")
    readonly_fields = ("uploaded_by",)
    show_change_link = True

# ========== MAIN ADMIN CLASSES ==========

class PersonAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # New instance
            last_person = Person.objects.aggregate(
                max_reg=models.Max('registration_number')
            )['max_reg']
            self.fields['registration_number'].initial = (last_person or 0) + 1
        from records.models import Center
        center_choices = [(center.name, center.name) for center in Center.objects.filter(is_active=True)]
        self.fields['structure'].widget = forms.Select(choices=[('', '---------')] + center_choices)
    class Media:
        js = ('assets/js/conditional_fields.js',)        
            

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    form = PersonAdminForm

    list_display = ('full_name', 'age_display', 'gender', 'municipality_display', 'mobile', 'neoplasm_count','request_count','knowledge_source')
    list_filter = ('gender', 'marital_status', 'municipality__regional_unit__region', 'created_at')
    search_fields = ('last_name', 'first_name', 'amka', 'mobile', 'email')
    readonly_fields = ('created_at', 'updated_at', 'calculated_age', 'bmi', 'bmi_category', 'neoplasm_links')
    
    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': (
                ('last_name', 'first_name'),
                ('father_name', 'mother_name'),
                ('birth_year', 'calculated_age', 'gender'),
                ('marital_status', 'children_count', 'minors', 'students', 'no_military_service'),
            )
        }),
        ('Ταυτότητα', {
            'fields': (
                ('nationality', 'citizenship'),
                ('vat', 'amka', 'id_card'),
            )
        }),
        ('Επικοινωνία', {
            'fields': (
                ('mobile', 'landline', 'email'),
                'address',
                ('city', 'postal_code'),
                ('region', 'regional_unit', 'municipality'),  # Updated this line
            )
        }),
        ('Διαχείριση', {
            'fields': (
                ('registration_number', 'structure', 'knowledge_source'),
                ('created_at', 'updated_at'),
            ),
        }),
        ('Ασφάλιση & Απασχόληση', {
            'fields': (
                ('insurance_status', 'insurance_provider', 'special_funds'), 
                ('status', 'widow_pension', 'disability_pension'),
                ('unemployment_card', 'unemployment_registration_date'),  # Only show when unemployed
                ('profession', 'specialization'),                          # Only show when employed
                ('employment_type', 'employer_name'),                      # Only show when employed
                ('employer_legal_form', 'hire_date'),                      # Only show when employed
                ('work_schedule', 'contract_type'),                        # Only show when employed
            )
        }),
        ('Διαχείριση Νεοπλασμάτων', {
            'fields': ('neoplasm_links',),
            'description': 'Χρησιμοποιήστε τους συνδέσμους παρακάτω για να διαχειριστείτε τα νεοπλάσματα του ωφελούμενου.'
        }),
        ('Φυσικά Χαρακτηριστικά', {
            'fields': (
                ('weight', 'height'),
                ('bmi', 'bmi_category'),
            ),
        }),
    )
      
    inlines = [
        ContactPersonInline,          # First - Contact persons
        NeoplasmInline,              # Fourth - Neoplasms (uncomment this)
        MedicalHistoryInline,        # Then medical history
        ComorbidityInline,           # Then comorbidities
        RequestInline,               # Then requests
        DocumentInline               # Finally documents
    ]
    
    def neoplasm_count(self, obj):
        try:
        # Try to use the reverse relationship
            neoplasms = obj.neoplasms.all()
        except AttributeError:
            # If relationship doesn't exist, query directly
            neoplasms = Neoplasm.objects.filter(person=obj)
        
        count = neoplasms.count()
        if count > 0:
            # Create a link to filtered neoplasm list
            url = reverse('admin:records_neoplasm_changelist') + f'?person__id__exact={obj.id}'
            # Get category breakdown for tooltip
            from collections import defaultdict
            categories = defaultdict(int)
            for neoplasm in neoplasms:
                category_name = neoplasm.icd10_category.name if neoplasm.icd10_category else "Άλλα"
                categories[category_name] += 1
            
            breakdown = ", ".join([f"{cat}: {count}" for cat, count in categories.items()])
            
            return format_html(
                '<a href="{}" style="color: #417690; font-weight: bold;" title="{}">'
                '📋 {} νεοπλάσματα</a>', 
                url, breakdown, count
            )
        else:
            # Create "Add Neoplasm" link
            add_url = reverse('admin:records_neoplasm_add') + f'?person={obj.id}'
            return format_html(
                '<a href="{}" style="color: #28a745; font-weight: bold;" title="Προσθήκη νέου νεοπλάσματος">'
                '➕ Προσθήκη</a>', 
                add_url
            )
    neoplasm_count.short_description = "Νεοπλάσματα"
    
    class Media:
        js = ('assets/js/cascading_dropdowns.js',)  # We'll create this
    
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
        neoplasms = obj.neoplasms.all()
        
        if not neoplasms.exists():
            add_url = reverse('admin:records_neoplasm_add') + f'?person={obj.id}'
            return format_html(
                '<a href="{}" style="color: #28a745; font-weight: bold;" title="Προσθήκη νέου νεοπλάσματος">'
                '➕ Προσθήκη</a>', 
                add_url
            )
        
        # Group by category for count
        from collections import defaultdict
        categories = defaultdict(int)
        
        for neoplasm in neoplasms:
            category_name = neoplasm.icd10_category.name if neoplasm.icd10_category else "Άλλα"
            categories[category_name] += 1
        
        # Create summary text
        total = neoplasms.count()
        url = reverse('admin:records_neoplasm_changelist') + f'?person__id__exact={obj.id}'
        
        # Show category breakdown in tooltip
        breakdown = ", ".join([f"{cat}: {count}" for cat, count in categories.items()])
        
        return format_html(
            '<a href="{}" style="color: #417690; font-weight: bold;" title="{}">'
            '📋 {} νεοπλάσματα</a>', 
            url, breakdown, total
        )

    neoplasm_count.short_description = "Νεοπλάσματα"
    
    def neoplasm_links(self, obj):
        if not obj.pk:
            return format_html('<em>Αποθηκεύστε πρώτα τον ωφελούμενο για να προσθέσετε νεοπλάσματα</em>')
        
        try:
            neoplasms = obj.neoplasms.all().order_by('-created_at')
        except AttributeError:
            neoplasms = Neoplasm.objects.filter(person=obj).order_by('-created_at')
        
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
        
        # Group neoplasms by category
        from collections import defaultdict
        categories = defaultdict(list)
        
        for neoplasm in neoplasms:
            category = neoplasm.icd10_category
            category_name = category.name if category else "Χωρίς κατηγορία"
            categories[category_name].append(neoplasm)
        
        # Build the display
        category_sections = []
        
        for category_name, category_neoplasms in categories.items():
            count = len(category_neoplasms)
            
            # Category header with count
            header = (
                f'<div style="background: #e3f2fd; padding: 8px 12px; margin: 8px 0 4px 0; '
                f'border-left: 4px solid #1976d2; border-radius: 4px;">'
                f'<strong style="color: #1976d2;">{category_name}</strong> '
                f'<span style="background: #1976d2; color: white; padding: 2px 8px; '
                f'border-radius: 12px; font-size: 12px; margin-left: 8px;">{count}</span>'
                f'</div>'
            )
            
            # Individual neoplasms in this category
            neoplasm_items = []
            for neoplasm in category_neoplasms:
                edit_url = reverse('admin:records_neoplasm_change', args=[neoplasm.id])
                
                # Build neoplasm info
                code_info = f"{neoplasm.icd10_code.code}" if neoplasm.icd10_code else "Χωρίς κωδικό"
                label_info = f"- {neoplasm.icd10_code.label}" if neoplasm.icd10_code else ""
                location_info = f"📍 {neoplasm.localization}" if neoplasm.localization else ""
                
                # Status indicators
                status_indicators = []
                if neoplasm.metastasis:
                    status_indicators.append('<span style="color: #dc3545;">🔴 Μεταστάσεις</span>')
                if neoplasm.surgery:
                    status_indicators.append('<span style="color: #28a745;">✅ Χειρουργείο</span>')
                
                status_text = " • ".join(status_indicators) if status_indicators else ""
                
                neoplasm_item = (
                    f'<div style="margin: 4px 0; padding: 8px; background: white; '
                    f'border: 1px solid #e9ecef; border-radius: 4px;">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                    f'<div>'
                    f'<strong style="color: #495057;">{code_info}</strong> {label_info}<br>'
                    f'<small style="color: #6c757d;">{location_info}</small>'
                    f'{f"<br><small>{status_text}</small>" if status_text else ""}'
                    f'</div>'
                    f'<a href="{edit_url}" target="_blank" '
                    f'style="padding: 4px 8px; background: #007bff; color: white; '
                    f'text-decoration: none; border-radius: 4px; font-size: 12px;">✏️ Επεξεργασία</a>'
                    f'</div>'
                    f'</div>'
                )
                neoplasm_items.append(neoplasm_item)
            
            # Combine header and items
            category_section = header + ''.join(neoplasm_items)
            category_sections.append(category_section)
        
        # Add "Add new" button
        add_url = reverse('admin:records_neoplasm_add') + f'?person={obj.id}'
        add_button = (
            f'<div style="margin: 15px 0; text-align: center;">'
            f'<a href="{add_url}" target="_blank" '
            f'style="display: inline-block; padding: 8px 16px; background: #28a745; color: white; '
            f'text-decoration: none; border-radius: 4px; font-weight: bold;">'
            f'➕ Προσθήκη νέου νεοπλάσματος</a>'
            f'</div>'
        )
        
        # Summary at the top
        total_count = neoplasms.count()
        category_count = len(categories)
        summary = (
            f'<div style="background: #fff3cd; padding: 10px; margin-bottom: 10px; '
            f'border-left: 4px solid #ffc107; border-radius: 4px;">'
            f'<strong>Σύνοψη:</strong> {total_count} νεοπλάσματα σε {category_count} κατηγορί{"ες" if category_count != 1 else "α"}'
            f'</div>'
        )
        
        return format_html(summary + ''.join(category_sections) + add_button)

    neoplasm_links.short_description = "Διαχείριση νεοπλασμάτων"
    
    def request_count(self, obj):
        count = obj.requests.count()
        if count > 0:
            url = reverse('admin:records_request_changelist') + f'?person__id__exact={obj.id}'
            return format_html('<a href="{}">{} αιτήματα</a>', url, count)
        return "0"
    request_count.short_description = "Αιτήματα"


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('person_name', 'tags_display', 'status', 'priority_display', 'submission_date', 'assigned_to', 'days_open_display')
    list_filter = ('status', 'primary_category', 'priority', 'communication_method', 'assigned_to', 'created_at')
    search_fields = ('person__last_name', 'person__first_name', 'subject', 'description')
    readonly_fields = ('created_at', 'updated_at', 'days_open', 'number_of_actions', 'update_date')
    
    filter_horizontal = ('tags',)
    inlines = [ActionInline, DocumentInline]
    
    # Use custom form if available
    if RequestForm:
        form = RequestForm
    
    fieldsets = (
        ('Βασικές Πληροφορίες', {
            'fields': (
                'person',
                'tags',
                'primary_category',
                'status',
                'priority',
            )
        }),
        ('Επικοινωνία', {
            'fields': (
                ('communication_method', 'contact_person_type'),
                ('submission_date', 'update_date'),
            )
        }),
        ('Περιεχόμενο', {
            'fields': (
                'subject',
                'outcome',
            )
        }),
        ('Διαχείριση', {
            'fields': (
                ('assigned_to', 'created_by'),
                ('due_date', 'closed_date'),
                ('protocol_number', 'is_accepted'),
                ('days_open', 'number_of_actions'),
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
    list_display = ("person", "icd10_code", "localization", "metastasis", "surgery")
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
            'fields': ('surgery', 'surgery_hospital')
        }),
        ('Θεραπεία', {
            'fields': ('scheduled_treatment',)
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

@admin.register(Therapy)
class TherapyAdmin(admin.ModelAdmin):
    list_display = ("neoplasm_info", "therapy_type", "hospital_name", "start_date")
    list_filter = ("therapy_type", "start_date", "neoplasm__icd10_category")
    search_fields = ("neoplasm__person__last_name", "neoplasm__person__first_name", "hospital_name")
    date_hierarchy = 'start_date'
    
    # Group by neoplasm
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'neoplasm__person', 
            'neoplasm__icd10_category', 
            'neoplasm__icd10_code'
        ).order_by(
            'neoplasm__person__last_name',
            'neoplasm__person__first_name', 
            'neoplasm__icd10_category__sort_order',
            '-start_date'
        )
    
    def changelist_view(self, request, extra_context=None):
        # Add custom context for grouping
        response = super().changelist_view(request, extra_context)
        
        # Group therapies by neoplasm
        if hasattr(response, 'context_data') and response.context_data:
            cl = response.context_data.get('cl')
            if cl and hasattr(cl, 'result_list'):
                grouped_results = self.group_therapies_by_neoplasm(cl.result_list)
                response.context_data['grouped_results'] = grouped_results
        
        return response
    
    def group_therapies_by_neoplasm(self, queryset):
        """Group therapies by neoplasm for display"""
        from collections import defaultdict
        grouped = defaultdict(list)
        
        for therapy in queryset:
            if therapy.neoplasm:
                neoplasm_key = f"{therapy.neoplasm.person} - {therapy.neoplasm.icd10_code}"
                grouped[neoplasm_key].append(therapy)
            else:
                grouped["Χωρίς νεόπλασμα"].append(therapy)
        
        return dict(grouped)
    
    def neoplasm_info(self, obj):
        if obj.neoplasm:
            person = obj.neoplasm.person
            category = obj.neoplasm.icd10_category.name if obj.neoplasm.icd10_category else "Κατηγορία"
            code = obj.neoplasm.icd10_code.code if obj.neoplasm.icd10_code else "Κωδικός"
            
            return format_html(
                '<div><strong>{}</strong><br>'
                '<small style="color: #666;">{} - {}</small></div>',
                person, category, code
            )
        return "-"
    neoplasm_info.short_description = "Ωφελούμενος & Νεόπλασμα"
    
    fieldsets = (
        ('Βασικά Στοιχεία', {
            'fields': ('neoplasm', 'therapy_type')
        }),
        ('Λεπτομέρειες', {
            'fields': ('hospital_name', 'start_date', 'notes')
        }),
    )


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    list_display = ("person", "disability", "certified_disability", "disability_percentage", "kepa_check", "kepa_expiry")
    list_filter = ("disability", "certified_disability", "kepa_check")
    search_fields = ("person__last_name", "person__first_name")
    
    # Add the conditional fields JavaScript
    class Media:
        js = ('assets/js/conditional_fields.js',)
    
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
            'classes': ('collapse',)
        }),
        # Add other fieldsets as needed
    )


@admin.register(Comorbidity)
class ComorbidityAdmin(admin.ModelAdmin):
    list_display = ("person", "diabetes", "cardiovascular_disease", "copd")  # Remove bmi fields
    list_filter = ("diabetes", "cardiovascular_disease", "copd")  # Remove bmi_category
    search_fields = ("person__last_name", "person__first_name")

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('request_link', 'action_display', 'action_date', 'organization_display', 'is_completed')
    list_filter = ('action_type', 'direction', 'contact_type', 'is_completed', 'action_date')
    search_fields = ('request__person__last_name', 'external_org__name', 'result')
    date_hierarchy = 'action_date'
    
    class Media:
        js = ('assets/js/action_cascading.js',)
        
    fieldsets = (
        ('Τύπος ενέργειας', {
            'fields': ('request', 'action_type', 'direction', 'contact_type', 'referral_type')
        }),
        ('Λεπτομέρειες', {
            'fields': ('action_date', 'performed_by')
        }),
        ('Εξωτερικός φορέας', {
            'fields': ('external_org', 'contact_person', 'manual_org_name', 'manual_contact_name'),
            'classes': ('collapse',)
        }),
        ('Αποτέλεσμα', {
            'fields': ('result', 'notes', 'is_completed', 'requires_follow_up', 'follow_up_date')
        }),
    )
    
    def action_display(self, obj):
        return str(obj)
    action_display.short_description = "Ενέργεια"
    
    def request_link(self, obj):
        url = reverse('admin:records_request_change', args=[obj.request.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.request))
    request_link.short_description = "Αίτημα"
    
    def organization_display(self, obj):
        return obj.organization_display
    organization_display.short_description = "Φορέας"


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

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['person', 'document_type', 'title', 'uploaded_by']
    list_filter = ['document_type', 'is_verified']
    search_fields = ['person__last_name', 'person__first_name', 'title']

#@admin.register(DocumentType)
#class DocumentTypeAdmin(admin.ModelAdmin):
#    list_display = ['name', 'is_required_for_requests']
#    list_filter = ['is_required_for_requests']
#    search_fields = ['name']

@admin.register(TherapyType)
class TherapyTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "therapy_category"]
    list_filter = ["therapy_category"]
    search_fields = ["name"]

# ========== ADMIN SITE CUSTOMIZATION ==========

admin.site.site_header = "K3 - Διαχείριση Ωφελούμενων"
admin.site.site_title = "K3 Admin"
admin.site.index_title = "Καλώς ήρθατε στο σύστημα K3"