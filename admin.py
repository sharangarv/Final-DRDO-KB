from django.contrib import admin
from .models import Laboratory, Tag, CrawlSession, RawPage, Article, Technology, Publication


@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display  = ['acronym', 'name', 'city', 'state', 'cluster']
    search_fields = ['name', 'acronym', 'city']
    list_filter   = ['state', 'cluster']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(CrawlSession)
class CrawlSessionAdmin(admin.ModelAdmin):
    list_display  = ['pk', 'status', 'started_at', 'finished_at',
                     'pages_crawled', 'pages_cleaned', 'pages_failed']
    list_filter   = ['status']
    readonly_fields = ['started_at', 'finished_at']


@admin.register(RawPage)
class RawPageAdmin(admin.ModelAdmin):
    list_display  = ['page_title', 'url', 'http_status', 'crawled_at', 'is_cleaned']
    list_filter   = ['is_cleaned', 'http_status', 'session']
    search_fields = ['url', 'page_title']
    readonly_fields = ['crawled_at']


class TechnologyInline(admin.StackedInline):
    model  = Technology
    extra  = 0


class PublicationInline(admin.StackedInline):
    model  = Publication
    extra  = 0


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display   = ['title', 'content_type', 'laboratory', 'word_count',
                      'published_date', 'is_duplicate']
    list_filter    = ['content_type', 'is_duplicate', 'language']
    search_fields  = ['title', 'full_text', 'source_url']
    filter_horizontal = ['tags']
    readonly_fields   = ['crawled_at', 'cleaned_at', 'updated_at', 'word_count']
    inlines           = [TechnologyInline, PublicationInline]
    date_hierarchy    = 'crawled_at'


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display  = ['technology_name', 'domain', 'trl_level']
    search_fields = ['technology_name', 'domain']
    list_filter   = ['domain', 'trl_level']


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display  = ['article', 'authors', 'journal', 'year']
    search_fields = ['authors', 'journal', 'doi']
    list_filter   = ['year']
