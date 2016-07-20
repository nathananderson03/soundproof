from __future__ import absolute_import
from django.contrib import admin
from .models import (
    User,
    InstagramImage,
    InstagramTag,
    Display,
    DisplayImage,
    DisplayFollowers,
    DisplayEngagementLog,
    PhotoFrame,
)

class DisplayImageAdmin(admin.ModelAdmin):
    list_display = ('display', 'image', 'approved')

class InstagramImageAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'tags__name',)
    list_display = (
        'remote_unixtime', 'remote_timestamp', 'created', 'user', 'tag_str'
    )

class InstagramTagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'max_tag_id')

class DisplayAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(DisplayAdmin, self).get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(admins=request.user)
        return qs
    exclude = ('tile_width', 'tile_margin')
    list_display = (
        'name', 'tags', 'active',
    )
    list_filter = ('active',)

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'last_updated')

class DisplayEngagementLogAdmin(admin.ModelAdmin):
    list_display = ('display', 'timestamp', 'total_image_count')
    list_filter = ('display',)

admin.site.register(Display, DisplayAdmin)
admin.site.register(DisplayEngagementLog, DisplayEngagementLogAdmin)
admin.site.register(DisplayFollowers)
admin.site.register(DisplayImage, DisplayImageAdmin)
admin.site.register(InstagramImage, InstagramImageAdmin)
admin.site.register(InstagramTag, InstagramTagAdmin)
admin.site.register(PhotoFrame)
admin.site.register(User, UserAdmin)
