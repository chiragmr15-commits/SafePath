from django.contrib import admin
from .models import UnsafeZone, CommunityReport

@admin.register(UnsafeZone)
class UnsafeZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'radius', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('name',)


@admin.register(CommunityReport)
class CommunityReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'is_verified', 'user', 'created_at')
    list_filter = ('severity', 'is_verified', 'created_at')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'latitude', 'longitude')
    
    actions = ['verify_reports', 'unverify_reports', 'delete_reports']
    
    def verify_reports(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} reports verified.')
    verify_reports.short_description = "Mark selected reports as verified"
    
    def unverify_reports(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} reports unverified.')
    unverify_reports.short_description = "Mark selected reports as unverified"
    
    def delete_reports(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} reports deleted.')
    delete_reports.short_description = "Delete selected reports"
