from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Article, Laboratory, Tag, CrawlSession


def dashboard(request):
    """Main KB dashboard with stats."""
    ctx = {
        'total_articles':    Article.objects.count(),
        'total_labs':        Laboratory.objects.count(),
        'total_tags':        Tag.objects.count(),
        'recent_sessions':   CrawlSession.objects.all()[:5],
        'type_breakdown':    Article.objects.values('content_type').annotate(n=Count('id')),
        'recent_articles':   Article.objects.select_related('laboratory')[:10],
    }
    return render(request, 'knowledge_base/dashboard.html', ctx)


def article_list(request):
    qs = Article.objects.select_related('laboratory').prefetch_related('tags')

    # Filters
    q    = request.GET.get('q', '')
    ctype = request.GET.get('type', '')
    tag  = request.GET.get('tag', '')

    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(full_text__icontains=q))
    if ctype:
        qs = qs.filter(content_type=ctype)
    if tag:
        qs = qs.filter(tags__name=tag)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    ctx = {
        'page_obj':   page_obj,
        'query':      q,
        'ctype':      ctype,
        'tag':        tag,
        'all_tags':   Tag.objects.all()[:50],
        'type_choices': Article.CONTENT_TYPE_CHOICES,
    }
    return render(request, 'knowledge_base/article_list.html', ctx)


def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'knowledge_base/article_detail.html', {'article': article})


def lab_list(request):
    labs = Laboratory.objects.annotate(n=Count('articles')).order_by('-n')
    return render(request, 'knowledge_base/lab_list.html', {'labs': labs})
