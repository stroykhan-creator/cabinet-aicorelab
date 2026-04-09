from django.contrib import admin
from .models import Product, ClientProfile, Treatment, CalculationTemplate, Proposal, ButtonAction

class TreatmentInline(admin.TabularInline):
    model = Treatment
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'base_price', 'wholesale_price', 'stock_qty', 'company')
    search_fields = ('sku', 'name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('patient', 'manager', 'phone', 'last_visit')
    search_fields = ('patient__name', 'manager', 'phone')
    inlines = [TreatmentInline]

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'procedure', 'date', 'doctor')
    search_fields = ('patient__name', 'procedure', 'doctor')

@admin.register(CalculationTemplate)
class CalculationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
    search_fields = ('name', 'description')

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'template', 'created_at')
    search_fields = ('client__name',)

@admin.register(ButtonAction)
class ButtonActionAdmin(admin.ModelAdmin):
    list_display = ('key', 'label', 'action_type', 'company')
    search_fields = ('key', 'label')
