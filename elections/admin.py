from django.contrib import admin

from models import Election, Candidate, PersonalInformation, Link

class CandidateInline(admin.StackedInline):
    model = Candidate
    extra = 1

class PersonalInformationInLine(admin.StackedInline):
	model = PersonalInformation
	extra = 1

class LinkInline(admin.TabularInline):
    model = Link
    extra = 1
>>>>>>> added: links section

class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    inlines = [CandidateInline]


class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at',)
    list_filter = ('last_name',)
    date_hierarchy = 'created_at'
    inlines = [PersonalInformationInLine,LinkInline]

admin.site.register(Election, ElectionAdmin)
admin.site.register(Candidate, CandidateAdmin)
